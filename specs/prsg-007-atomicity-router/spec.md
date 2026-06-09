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

- **Unreadable or missing input**: When a requested input file (`tasks.md`, `plan.md`, or
  `spec.md`) is missing or unreadable, the classifier reports a usage/input error rather
  than emitting a route, and signals this through its non-success exit status (never a
  block of the workflow).
- **No discernible signal at all**: When none of the detectors find a decisive signal, the
  classifier abstains to the default route `one-navigable-PR` — it never auto-splits and
  never blocks.
- **Conflicting signals**: When a split-PR signal (multiple seams) coexists with a
  hard-atomic signature, the hard-atomic override wins and the route is `single-atomic-PR`.
- **Change is entirely outside the governed scope**: When the change does not fit any
  splittable or atomic category the router governs, it emits the `out-of-scope` route so
  the autopilot can fall back to its default single-PR behavior.
- **Contextual probe signal present but shallow**: When a flag-system, release-cadence, or
  consumer-locality signal is detected, it is surfaced only as an advisory hint and does
  not, on its own, force a split — the three fully-implemented detectors decide the route.

## Requirements *(mandatory)*

### Functional Requirements

#### Core classifier (fully implemented)

- **FR-001**: The classifier MUST accept a feature's `tasks.md`, `plan.md`, and `spec.md`
  as inputs and emit exactly one routing decision drawn from the fixed set: `split-PR`,
  `one-navigable-PR`, `branch-by-abstraction`, `single-atomic-PR`, `out-of-scope`.
- **FR-002**: The classifier MUST decide splittability by **structural seams** (multiple
  independent additive capabilities or surfaces), NOT by lines of code; it MUST NOT compute
  or rely on any LOC/sizing metric.
- **FR-003**: The classifier MUST apply detectors in this order: (1) `tasks.md` shape,
  (2) additive-vs-modify, (3) flag-system probe, (4) release cadence, (5) consumer
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
  hard-atomic signature — exported-symbol rename, global version pin, destructive
  migration, mutual-exclusion/auth/payment primitive, or out-of-tree contract break — it
  MUST route the change to `single-atomic-PR`, overriding any split-PR signal.
- **FR-008**: The classifier MUST detect destructive-migration and concurrency signatures
  and, for those classes, mark the result not releasable AND attach a warning that a
  passing CI run does not prove the change is releasable ("CI-green ≠ releasable").
- **FR-009**: For changes with no releasability-risk signature, the classifier MUST mark
  the result releasable and attach no CI-green warning.

#### Contextual probes (advisory hints only)

- **FR-010**: The classifier MUST emit the flag-system probe, release-cadence, and
  consumer-locality detectors as **advisory hints only** — surfaced in the result but not
  deeply implemented, and not, on their own, sufficient to force a split. (Deep
  implementation of these three probes is out of scope for this spec — see Out of Scope.)

#### Output, advisory contract, and recording

- **FR-011**: The classifier MUST be read-only: it MUST emit exactly one machine-readable
  result to standard output and MUST write no files of its own.
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

- **Routing decision**: The single result the classifier emits. Attributes: the chosen
  route (one of `split-PR`, `one-navigable-PR`, `branch-by-abstraction`, `single-atomic-PR`,
  `out-of-scope`); a releasability flag; an optional CI-green warning; and advisory hints
  from the three shallow probes.
- **Change class**: The category a change falls into as read from its artifacts — e.g.
  additive multi-seam, modify-heavy, hard-atomic (rename / version pin / destructive
  migration / mutual-exclusion-auth-payment primitive / out-of-tree contract break), or
  concurrency-sensitive. Each class maps to a route and a releasability reading.
- **Atomicity Route record**: The "## Atomicity Route" section the autopilot SKILL writes
  into the workflow file from the emitted decision, for downstream specs to read. (Written
  by the SKILL, not by the classifier.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every governed change class, the classifier emits exactly one route from
  the fixed set of five, in a single machine-readable result.
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
- **No internal call to, and no edit of, the existing reviewability gate; no shared-library
  extraction** in this spec.
- **The route is NOT stored in `SPEC-MOC.md`** — only in the workflow file's "## Atomicity
  Route" section.
