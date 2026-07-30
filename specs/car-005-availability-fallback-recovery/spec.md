# Feature Specification: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Feature Branch**: `car-005-availability-fallback-recovery`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "CAR-005 Model Availability, Fallback, and Recovery Simulation — prove bounded route-resolution and recovery semantics synthetically, before CAR-006 implements the real resolver, via an executable reference simulator plus a deterministic fixture corpus that pins how resolution must behave when a preferred model is absent, an effort is unsupported, a probe is unavailable or fails, an alias re-points, the platform changes a route, an environment carries an unqualified override, the optional helper is unavailable, or no safe route exists."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolution-failure semantics (Priority: P1)

The routing program needs a single, provable answer to "what happens when the
preferred model is not there?" before any real route policy exists. This story
delivers the environment-snapshot projection, the route-policy fixture shape,
the ordered preferred-then-fallback resolution walk, the five pinned resolution
reason codes with machine-readable sub-reasons, and byte-identical deterministic
replay against pinned expected reports.

**Why this priority**: P1 because every later behavior in this feature — and
CAR-006's production resolver — is expressed in terms of the report contract and
the reason-code vocabulary this story establishes. Without it there is nothing
for structural rejections or recovery paths to be reported *in*.

**Independent Test**: Fully testable by running the reference simulator over the
resolution-failure cases in the scenario corpus and asserting each produced
report is byte-identical to that case's pinned expected report. Delivers value
on its own: CAR-006 can adopt the snapshot projection, report contract, and
reason-code enum even if nothing else in this feature lands. The projection is
**CAR-006's preflight input contract** — the shape its live capability capture must
project into — which is why FR-002 states sufficiency in both directions and why a
vestigial member here would be inherited debt rather than a local cost.

**Acceptance Scenarios**:

1. **Given** a policy whose preferred route names a model absent from the
   synthetic snapshot and whose first fallback is present and compatible,
   **When** resolution runs, **Then** the report resolves to the fallback route,
   records both attempted routes in attempt order, and emits a
   `preferred_model_unavailable` diagnostic whose `details` carry the
   `model_absent` sub-reason.
2. **Given** a policy whose preferred route names the `fable` alias and a
   snapshot in which that alias resolves to no available model, **When**
   resolution runs, **Then** the report emits `preferred_model_unavailable` and
   continues the ordered fallback walk rather than failing outright.
3. **Given** a snapshot in which the preferred model is available but its
   supported-efforts list omits the policy's declared effort, **When**
   resolution runs, **Then** the report emits `effort_unsupported` naming both
   the declared effort and the model's supported efforts.
4. **Given** a snapshot marking capability probing unavailable for a candidate
   route, **When** resolution runs, **Then** the report emits
   `capability_probe_unavailable` for that route and does not treat probe
   absence as probe success.
5. **Given** a snapshot whose exact-invocation probe outcome for a candidate
   route is a failure, **When** resolution runs, **Then** the report emits
   `treatment_probe_failed` for that route and the route is not selected.
6. **Given** a snapshot whose exact-invocation probe outcome for the preferred
   route is a success, **When** resolution runs, **Then** the preferred route is
   selected, no resolution diagnostic is emitted, and the report records the
   effective dispatch tuple.
7. **Given** a policy pinning an alias-plus-resolved-model tuple and a snapshot
   in which that alias now binds to a different resolved model ID, **When**
   resolution runs, **Then** the report emits `preferred_model_unavailable` with
   the `alias_repointed` sub-reason rather than silently accepting the new
   binding.
8. **Given** a snapshot representing a platform-side route change for a pinned
   tuple, **When** resolution runs, **Then** the report emits
   `preferred_model_unavailable` with the `platform_route_changed` sub-reason.
9. **Given** any resolution-failure case in the corpus, **When** the simulator is
   run twice over the identical inputs, **Then** both serialized reports are
   byte-identical to each other and byte-identical to that case's pinned
   expected report under canonical JSON serialization.

---

### User Story 2 - Structural rejection and recovery semantics (Priority: P2)

The routing program needs the defective-policy and degraded-environment cases
pinned too: policies that loop, substitute an unqualified adjacent model,
substitute a generic agent, or silently inherit an unpinned route must be
rejected with their own closed codes; unqualified environment overrides and an
unavailable optional helper must behave exactly as contracted; and declared
probe/retry/fan-out budgets must exhaust deterministically into a report-only
no-safe-route outcome carrying rollback remediation.

**Why this priority**: P2 because it depends on the report contract and
reason-code envelope established by User Story 1, and stacks on it as the second
PR in the delivery chain. It completes the recovery half of the roadmap scope.

**Independent Test**: Fully testable by running the reference simulator over the
structural-rejection, override, helper-unavailable, and budget-exhaustion cases
in the scenario corpus and asserting each produced report is byte-identical to
that case's pinned expected report. Delivers value on its own: CAR-006 and the
cohort specs inherit proven rejection semantics.

**Acceptance Scenarios**:

1. **Given** a policy whose fallback chain revisits a route already attempted,
   **When** resolution runs, **Then** the policy is rejected with a
   `fallback_loop` diagnostic and the walk terminates without repeating the
   revisited route.
2. **Given** a policy whose fallback names a model adjacent to a qualified route
   but not itself qualified, **When** resolution runs, **Then** the policy is
   rejected with an `unqualified_adjacent_model` diagnostic and that fallback is
   never selected.
3. **Given** a policy whose fallback replaces a named synthetic agent with a
   generic agent, **When** resolution runs, **Then** the policy is rejected with
   a `generic_agent_substitution` diagnostic.
4. **Given** a policy whose route omits an explicit model or effort so the value
   would be materialized by inheritance, **When** resolution runs, **Then** the
   policy is rejected with a `silent_inherit_materialization` diagnostic.
5. **Given** a synthetic environment carrying an unqualified subagent-model
   override, **When** resolution runs, **Then** the report records the override
   as the effective dispatch tuple, emits an `unqualified_override` diagnostic,
   marks the environment excluded from release claims, and additionally records
   the qualified resolution that would have applied without the override.
6. **Given** a snapshot in which the optional helper's routes are unavailable,
   **When** resolution runs, **Then** the helper is not consulted, the report
   records continuation on the validated no-helper path, and resolution of
   required agents does not fail.
7. **Given** a policy declaring a probe or retry budget of one and a snapshot in
   which the first attempt fails, **When** resolution runs, **Then** the report
   records exactly one attempt, does not exceed the declared cap, and reports
   the actual attempt count alongside the declared budget.
8. **Given** a policy whose preferred route and every declared fallback are
   rejected, **When** resolution runs, **Then** the report is report-only: it
   names the unresolved agent, every attempted route, each rejection reason, and
   remediation whose actions include rolling back to the previous plugin
   release — and no shipped agent file is read for mutation or written.
9. **Given** any structural-rejection, override, helper, or exhaustion case in
   the corpus, **When** the simulator is run twice over the identical inputs,
   **Then** both serialized reports are byte-identical to each other and
   byte-identical to that case's pinned expected report.

---

### Edge Cases

- A route is rejected for more than one reason at once (for example, the model
  is present but the effort is unsupported *and* the exact-invocation probe
  failed): the report must be deterministic about which diagnostics are emitted
  and in what order, so replay stays byte-identical. **FR-012b pins both** — one
  diagnostic per failed check, sequenced by the FR-005 declaration order — so this
  example resolves to `effort_unsupported` then `treatment_probe_failed`.
- An unqualified override is present *and* no qualified route resolves: the
  report must still record the override as effective, still mark the environment
  excluded from release claims, and still report the would-have-been outcome as
  `no_safe_route`. FR-024a pins the three consequences: `outcome` follows the
  qualified walk rather than the override, `release_claim_eligible` is `false`, and the
  would-have-been dispatch tuple is **omitted** rather than `null`.
- The optional helper is unavailable *and* a required agent is also unresolvable:
  helper unavailability must not mask or soften the required agent's
  `no_safe_route` outcome.
- A policy declares a budget above the schema-enforced maximum: the fixture must
  fail schema validation rather than be silently clamped at run time.
- A fallback list is empty: the preferred route's rejection must lead directly to
  `no_safe_route` rather than an ambiguous empty-walk outcome.
- An alias re-point makes the newly bound model one that *is* otherwise
  qualified: the pinned tuple is still unavailable, so the route is still
  rejected rather than opportunistically accepted.

## Requirements *(mandatory)*

### Functional Requirements

#### Simulator and input contracts (User Story 1)

- **FR-001**: The system MUST provide an executable reference simulator, located
  in the Layer 6 efficiency test library alongside the existing Claude
  simulators, that behaves as a pure function from (route policy, synthetic
  environment snapshot, environment overrides, declared budgets) to a resolution
  report, with no filesystem, network, wall-clock, or randomness input. [US1]
  The simulator MUST be a **single** module, created in slice 1 and extended
  additively in slice 2. Structural policy validation MUST NOT be a second module:
  it is a second rule family inside the one resolution walk, and `fallback_loop`
  detection needs the walk state that this module already owns. Slice 2 MUST add new
  module-level constants, new private helpers, and new public entry points, and MUST
  change no slice-1 function signature. [US1] [US2]
- **FR-002**: The system MUST define a minimal, purpose-built environment
  snapshot projection carrying only what resolution consumes, which is **seven**
  facts and not the five an earlier reading of this requirement listed: available
  model IDs, alias-to-resolved-model bindings, per-model supported efforts, probe
  availability, exact-invocation probe outcomes, **declared platform route changes
  for pinned tuples**, and **the organization model allowlist**. It MUST NOT reuse
  the CAR-002 runtime-capability-snapshot capture-record shape. [US1]
  The last two are named because each is read by a requirement that is otherwise
  unsatisfiable from the projection, and this requirement is simultaneously the
  stated authority on the projection's shape — so an incomplete list here is not a
  summary but a defect:
  - **Declared platform route changes** are what FR-006's `platform_route_changed`
    sub-reason reads. That sub-reason's predicate is "the snapshot declares a
    platform-side route change for the pinned tuple", so the declaration has to be
    a projection member for the predicate to have anything to evaluate.
  - **The organization model allowlist** is what FR-024b's override-skip branch
    reads. The documented runtime checks an override value against the allowlist
    and skips one that resolves to an excluded model, so an override's effect on
    dispatch is not derivable without it.

  **Sufficiency is claimed in both directions**, and both halves are checkable
  against the consumed-by column in `data-model.md` §2: no requirement reads a fact
  the projection omits, and no projection member lacks a named consuming
  requirement. A member with no consumer would be dead contract that CAR-006
  inherits under FR-002's own minimality claim, which is the cost this
  bidirectional reading exists to prevent.
- **FR-002a**: The projection's provenance and its **epistemic status** MUST be
  recorded, because the roadmap makes the CAR-002 probed unavailable-model
  behaviour the input that "shapes the CAR-005 reason codes"
  (`docs/ai/specs/claude-agent-routing-technical-roadmap.md:420-421`) and this
  feature would otherwise claim an alignment it cannot demonstrate. [US1]
  - **Unavailability is a snapshot-declared preflight input, never a simulated
    dispatch attempt.** Every unavailability this feature reports is read from the
    projection by the pure function FR-001 mandates. No requirement here simulates,
    predicts, or encodes what a dispatch against an absent model would do. This
    follows from FR-001's no-network purity and FR-008's refusal to read probe
    absence as probe success, and it is stated as a requirement anyway because the
    dispatch-outcome fact is **not settled** (below) — so an artifact that appeared
    to encode one would assert more than the program knows.
  - **What CAR-002 actually froze is a three-member vocabulary over two surfaces.**
    The committed probe classifies an unavailable-model observation as
    `hard_rejection`, `soft_remap`, or `undetermined`, across the `print_model` and
    `subagent_frontmatter` surfaces
    (`tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py:77`,
    `:829-851`, `:901-934`). That is **not** the binary "hard error versus silent
    substitution" the roadmap anticipated, and `undetermined` is a first-class
    recorded value carrying the explicit reading that no availability claim derives
    from it.
  - **Its status is labeled inference and open, not pinned fact.** That probe emits
    its unavailable-model answer with `"label": "labeled_inference"` where the
    alias-binding answers carry `"label": "observation"`, and reports `status`
    `answered` only when some surface returned a non-`undetermined` outcome; the
    route-change-detection answer is hardcoded `status: "open"`
    (`claude_capabilities.py:1061-1102`), because inducing a re-point collides with
    the same unset-proof that keeps the environment clean. No committed capture in
    the tree carries an actual observed outcome. **This feature therefore pins
    resolution semantics *ahead of* the platform fact rather than downstream of
    it.** That is coherent for a synthetic simulation — the corpus is the contract
    and CAR-006 re-proves its resolver against it — but it MUST be stated rather
    than glossed, so no reader infers that a determinate platform observation
    stands behind these five codes.
  - **The surface is `subagent_frontmatter`, and the mapping is one-way and total
    on the CAR-002 side.** This feature routes named subagents, so the projection's
    exact-invocation values project that surface — the one CAR-002 itself reads as
    inference rather than certified fact. The mapping from CAR-002's three outcomes
    onto projection members MUST be declared in `data-model.md` §2 and MUST leave
    no CAR-002 outcome unrepresented. In particular `undetermined` MUST NOT map to
    a probe success or to a silently selectable route: it maps to probe
    unavailability, so FR-008 governs it. Fail-closed here is the same rule FR-008
    already imposes one field over — an observation from which no availability
    claim derives is at least as weak as an absent probe. No new enum member is
    required: all three CAR-002 outcomes land on projection members this
    requirement already names.
- **FR-003**: The system MUST define a route-policy fixture contract expressing,
  per named synthetic agent, a preferred route (alias, qualified resolved model
  ID, and explicit effort), an ordered list of qualified fallback routes, declared
  probe, retry, and fan-out budgets, and — optionally — the policy's declared
  optional helper with its own routes (FR-025b). [US1]
- **FR-003a**: The route-policy schema MUST be deliberately **permissive about the
  defects this feature exists to diagnose**, because a schema strict enough to reject
  them would make the requirements that simulate them unsatisfiable: [US1] [US2]
  - A route's `resolved_model` and `effort` MUST remain **optional**. FR-023 requires a
    policy whose route omits an explicit model or effort to be rejected at *resolution*
    with `silent_inherit_materialization`. If the schema required those fields, the
    fixture would fail *schema validation* instead and no diagnostic would ever be
    produced.
  - `fallback_routes` MUST NOT declare `uniqueItems`. FR-020 requires a policy whose
    fallback chain revisits an already-attempted route to be rejected at resolution with
    `fallback_loop`. `uniqueItems` would reject that fixture at schema-validation time,
    again pre-empting the diagnostic.
  - FR-027 is the deliberate **inverse** case: an out-of-range *declared budget* is
    meant to fail schema validation rather than surface as a diagnostic, which is why
    the budget maxima are enforced in the schema while these two constraints are not.

  The dividing rule: defects the simulator must *diagnose* stay representable in the
  schema; defects that are simply *invalid input* are rejected by it.
- **FR-004**: Resolution MUST walk the preferred route first and then the
  declared fallbacks in their declared order, selecting the first compatible
  route, and the report MUST record every attempted route in attempt order. [US1]

#### Resolution reason codes (User Story 1)

- **FR-005**: The system MUST define a closed route-resolution reason-code enum
  whose members are exactly, and verbatim, the five codes the Claude routing
  roadmap pins: `preferred_model_unavailable`, `effort_unsupported`,
  `capability_probe_unavailable`, `treatment_probe_failed`, and `no_safe_route`.
  The enum MUST NOT be extended by this feature. [US1]
- **FR-006**: A route whose pinned tuple is unavailable MUST be reported as
  `preferred_model_unavailable` carrying a machine-readable sub-reason in the
  diagnostic's `details` object. The sub-reason vocabulary is the closed
  **four-member** set below, evaluated in this order so exactly one member applies to
  any snapshot and replay stays byte-identical: [US1]
  - **`alias_unresolved`** — the route's pinned alias has no binding at all in the
    snapshot's alias-to-resolved-model table.
  - **`alias_repointed`** — the alias is bound, but to a resolved model ID other than
    the one the route pins.
  - **`model_absent`** — the alias binds exactly as pinned, but the pinned resolved
    model ID is not among the snapshot's available model IDs.
  - **`platform_route_changed`** — the snapshot declares a platform-side route change
    for the pinned tuple.

  These four are **total** over the FR-002 projection — any unavailable pinned tuple
  matches at least one — and the ordered walk yields exactly one. Their exclusivity is
  **not uniform**, and the difference is load-bearing rather than cosmetic:
  - The first three are **structurally disjoint**, because their predicates partition
    the state of a single snapshot field. The alias is either unbound
    (`alias_unresolved`), bound to some other model (`alias_repointed`), or bound
    exactly as pinned (`model_absent`'s precondition). No snapshot satisfies two.
  - `platform_route_changed` reads a **separate** snapshot field, so it can co-occur
    with any of the first three. Its disjointness is produced by the evaluation
    order — it is tested last and only reached when all three prior predicates miss.
    The order is therefore the mechanism that makes the vocabulary single-valued, not
    a tie-breaking nicety, and it MUST be structural in the simulator (a staged call
    graph) rather than a comment that a later edit can reorder.

  **Consequence for the corpus, which MUST be honoured when the case is authored:**
  a case intended to pin `platform_route_changed` MUST bind its alias exactly as the
  route pins it *and* list the pinned resolved model among the available models, so
  the three earlier predicates all miss. A snapshot that merely declares a
  platform-side route change while also repointing the alias, or while omitting the
  model, resolves to `alias_repointed` or `model_absent` instead — and because the
  case's expected report is pinned by hand, that mismatch surfaces as a replay
  failure whose stated cause looks unrelated to how the snapshot was built.

  `alias_unresolved` is a fourth member
  rather than a fold into `model_absent` because it is a reachable input that neither
  other member can describe — `alias_repointed`'s `details` must name a
  pinned-versus-observed model pair and there is no observed model, and
  `model_absent`'s `details` must name the missing resolved model ID and none was ever
  resolved. Folding it in would emit a diagnostic with an empty model field, which is
  an unreported input class inside a supposedly closed vocabulary and a determinism
  hazard. The input cannot be forbidden by schema, because the policy and the snapshot
  are separate documents within one case and a cross-document key constraint is not
  expressible. The `fable` case required by FR-010 exercises **`model_absent`** — the
  roadmap subordinates it to preferred-model-absent ("including a `fable`-unavailable
  case"). The corpus MUST additionally include one `alias_unresolved` case.

  **The vocabulary's fidelity to the platform MUST be recorded, not only its
  totality over the projection.** Totality over a projection this feature authors is
  a closed loop; what a reviewer needs is that the projection's input classes are the
  real ways a pinned tuple goes stale.
  - **Alias re-pointing is documented behaviour, so `alias_repointed` rests on a
    real hazard.** Aliases point to the recommended version for the provider and
    **update over time**; pinning requires the full model name or a per-family
    environment override. The published documentation records re-points having
    actually occurred, with version fences on the `opus` family. `fable` is likewise
    a real documented family alias, so FR-010's case names a real one.
  - **Three documented vectors, one observation.** An alias's binding can move by
    (a) provider-side version drift, (b) per-family environment redefinition, and
    (c) allowlist substitution to the newest permitted version of the family. The
    sub-reason is deliberately **cause-agnostic**: all three vectors present
    identically in the projection as "the alias binds to a resolved model ID other
    than the one the route pins", because the projection records the *binding*, not
    the mechanism that moved it. No fourth member is needed and none may be added —
    a cause the projection cannot distinguish cannot be a sub-reason it reports.
    Vector (b) is independently corroborated in-tree: CAR-002 records that inducing
    a re-point requires exactly such a per-family override and that this "structurally
    collides" with its own unset proof, which is *why* its route-change question is
    left open (`claude_capabilities.py:482-487`).
  - **Recorded limitation, bounded deliberately.** Allowlist substitution is
    provider-dependent — some providers substitute and announce, others reject or
    replace outright — so the same organizational configuration can present as a
    re-point on one provider and as an absent model on another. The projection
    carries no provider identity and MUST NOT gain one: which provider an
    environment ran against is upstream of resolution and belongs to CAR-006's live
    preflight, not to a synthetic replay whose snapshot is already the observed
    outcome. What the projection records is what was observed, whichever provider
    produced it. This is a stated boundary, not an unexamined one.
  - **Reconciliation with CAR-002's detection rule.** CAR-002 defines platform
    route-change detection as "any observed model ID differing from the resolved
    qualified ID, **including alias re-pointing**", recorded separately from
    resolver fallback (`claude-agent-routing-technical-roadmap.md:432-435`) — one
    bucket where this vocabulary has two members. The two are **not** in conflict,
    and the relationship MUST be stated because the appearance of conflict is
    otherwise the natural reading. CAR-002's rule is a *detection* rule with one
    disposition; this vocabulary is a *reporting* refinement that sub-divides that
    single bucket by **which snapshot field evidences the divergence** — the alias
    table moved (`alias_repointed`), or the binding is intact and a route change is
    declared against the pinned tuple (`platform_route_changed`). The union of the
    two members is exactly CAR-002's bucket, so nothing CAR-002 detects goes
    unreported and nothing is double-counted. The sub-division is a **contract
    decision made ahead of the platform fact**, not an observed distinction: CAR-002's
    route-change answer is hardcoded open (FR-002a), so no capture exists that could
    have distinguished the two at execution time.
- **FR-007**: A route whose model is available but whose declared effort is not
  in that model's supported efforts MUST be reported as `effort_unsupported`,
  naming both the declared effort and the model's supported efforts. [US1]
- **FR-007a**: The **effort vocabulary** and the **relationship between this
  requirement and documented runtime behaviour** MUST both be stated. Neither is
  today: the ladder is fixed only in `data-model.md` and sourced to an in-tree
  frozen contract, and FR-007's rejection semantics were never reconciled with what
  the runtime does with an unsupported effort. [US1]
  - **The ladder is closed at five members, in this order:** `low`, `medium`,
    `high`, `xhigh`, `max`. It reuses the frozen ordered ladder the successor
    capability contract already pins
    (`contracts-claude/successor-capability-freeze.schema.json:166-169`, described
    there as "the closed ordered Claude ladder"), so this feature introduces no
    parallel effort vocabulary that would make FR-007's case untranslatable when
    CAR-006 adopts the corpus.
  - **Its scope is the subagent-frontmatter surface**, which is the surface this
    feature routes. Those five are exactly the documented options for a subagent's
    `effort` field. `ultracode` is deliberately **not** a member and its absence is
    not an omission: it is a session-level orchestration setting accepted by the
    interactive effort command rather than a model effort level — it sends `xhigh`
    to the model and additionally has the client orchestrate dynamic workflows —
    and it is not among the subagent `effort` options
    (`docs/ai/research/claude-agent-route-candidates.md:605-611`, `EFF-1`/`EFF-2`).
    Recording the scope is what stops a reader from treating a session-only value as
    a missing member of a supposedly closed ladder.
  - **A third closed enum needs the drift protection the other two already have.**
    The two reason-code vocabularies receive exact set-equality assertions read live
    by JSON pointer (FR-017a, FR-019b); the effort ladder is a third closed enum in
    the same shipped schemas and had none, so a sixth member or a dropped member
    would fail nothing. Slice 1's test MUST therefore assert exact set equality
    between the route schema's effort enum and these five members, failing in both
    directions. Unlike FR-017a and like FR-019b, the expected members are declared
    in the test file, and for the same reason: the second independent committed
    witness is the frozen successor-capability contract, and a test-side literal
    plus that contract is what makes drift detectable at all.
  - **Per-model effort support is a real documented constraint, not an invention.**
    The subagent `effort` field's documented option list carries the qualifier
    "available levels depend on the model" (`EFF-1`), and the constraint has real
    instances rather than being merely theoretical: current models divide into those
    supporting all five, those omitting `xhigh`, and those supporting no effort
    level at all. FR-007's `effort_unsupported` therefore models a live platform
    constraint, and the projection's per-model supported-efforts map (FR-002) is the
    faithful shape for it.
  - **Rejection is a deliberate preflight policy, not a mirror of runtime
    rejection.** The runtime does **not** fail an unsupported effort: it falls back
    to the highest supported level at or below the one declared, and an
    organization-level effort cap clamps the same way — silently under the
    machine-readable output formats a harness uses. This requirement nevertheless
    rejects the route at preflight, and the divergence is the point rather than an
    oversight: a route whose declared effort silently degrades is **not a qualified
    route**, because the tuple that actually ran is not the tuple the policy pinned
    and no report field would record the difference. A qualification program whose
    whole purpose is attributable treatment cannot rest on a silent downgrade. The
    honest statement is therefore that `effort_unsupported` is a **preflight
    qualification failure**, and this feature refuses at preflight what the runtime
    would paper over at dispatch. Stating it is what keeps the corpus from appearing
    to prove a runtime rejection that does not exist — the same fidelity obligation
    FR-024b carries for the override.
  - **Recorded reproducibility note.** The effort scale is calibrated per model, so
    one level name does not denote the same underlying value across models. Combined
    with alias drift (FR-006), an alias-plus-effort pin is doubly unstable, which is
    independent support for FR-003's insistence that a route pin a **qualified
    resolved model ID** and not an alias alone.
- **FR-008**: A route whose candidate model has capability probing marked
  unavailable in the snapshot MUST be reported as
  `capability_probe_unavailable`, and probe absence MUST NOT be treated as probe
  success. [US1]
- **FR-009**: A route whose exact-invocation probe outcome in the snapshot is a
  failure MUST be reported as `treatment_probe_failed` and MUST NOT be selected.
  [US1]
- **FR-010**: The scenario corpus MUST include a case in which the preferred
  route names the `fable` alias and that alias is unavailable in the snapshot.
  [US1]
- **FR-011**: The scenario corpus MUST include a case in which the
  exact-invocation probe succeeds and the preferred route is selected with no
  resolution diagnostic emitted. [US1]

#### Report and diagnostics shape (User Story 1)

- **FR-012**: Every rejection and remediation entry in the resolution report
  MUST use the installed runner's diagnostics envelope shape — `code`,
  `message`, `severity`, `source`, `details`, and `remediation` with `summary`
  and `actions` — with `code` drawn from one of this feature's two closed enums.
  No second diagnostics dialect may be introduced. [US1]
  Within the diagnostic definition, `code`, `message`, `severity`, `source`, and
  `remediation` are **required** and `details` is **optional**, mirroring the installed
  runner, which always emits the first five (substituting default remediation when the
  caller passes none) and emits `details` only when non-empty. `severity` is closed to
  `info`, `warning`, `error`, matching the runner's own diagnostic validator. The same
  `if`/`then` idiom MUST make `details` required for **every one of the eight
  route-scoped codes FR-029a names**, and MUST additionally require `route_id` *within*
  `details` on each — a branch that requires only the container leaves the key itself
  optional, which is no key at all. That is **eight branches, four in each diagnostic
  `$defs`**: in `resolutionDiagnostic` for `preferred_model_unavailable` (FR-006),
  `effort_unsupported` (FR-007), `capability_probe_unavailable` (FR-008), and
  `treatment_probe_failed` (FR-009); in `policyViolationDiagnostic` for `fallback_loop`
  (FR-020), `unqualified_adjacent_model` (FR-021), `generic_agent_substitution`
  (FR-022), and `silent_inherit_materialization` (FR-023). The first two additionally
  require the payload FR-006 and FR-007 name. `unqualified_override` is the one member
  of either enum that takes no branch: it is an environment condition scoped to no
  route (FR-019c), so it has no route key to carry. `remediation` is a field of each
  diagnostic entry, **never** a top-level report field — hoisting it would create the
  second dialect this requirement forbids.
  Note the trap: a different diagnostics dialect exists elsewhere in the tree (an
  autopilot gate-state contract that requires `details` and omits `remediation`, the
  inverse of the runner). FR-012 binds to the installed **runner**; that other contract
  MUST NOT be copied as the precedent.
- **FR-012a**: Every `remediation.actions` entry MUST be drawn from a **single closed
  enum of literal strings** with exactly one declaration site in the resolution-report
  schema, located **inline** at `$defs/remediation/properties/actions/items/enum`.
  *(Corrected during Plan: an earlier draft of this requirement named a bare
  `$defs.remediationAction` member, which directly contradicts FR-016a — verified
  empirically that zero of the eleven documents in this directory has a `$defs` member
  carrying a top-level `enum`, so such a member would be the first and would break the
  very invariant FR-016a cites. The two requirements could not both be satisfied
  literally. Inlining preserves everything FR-012a is for — one closed set, literal
  strings, a single declaration site, and a stable JSON pointer for set-equality
  assertions; only the `$defs` name is given up, and `/items/enum` nested under a
  `$defs` object is already an existing shape in this directory.)* Entries MUST NOT be structured objects — the runner types
  this field as a list of plain strings, and changing its shape is the second dialect
  FR-012 forbids — and MUST NOT be templates with substitution slots, because closure
  would then degrade from set equality to one regex per template, weakening SC-003 for
  the one field SC-010 depends on. Case-specific values (the missing model ID, the
  declared and supported efforts, the observed alias binding) are carried in the
  diagnostic's `details` object, never interpolated into an action string, so a
  consumer acts on set membership without parsing prose. The `actions` array MUST
  declare `minItems: 1` and `maxItems: 3`, mirroring the installed runner, which always
  substitutes at least one default action and hard-truncates the list to three — a
  fourth action would be silently discarded by the real runner. The `no_safe_route`
  diagnostic's `actions` MUST include the member
  `Roll back to the previous plugin release.` **verbatim**, which is the imperative
  rendering of the rollback guidance the roadmap states in both the CAR-005 scope and
  the downstream live-UAT scope. [US1] [US2]
- **FR-012b**: Diagnostic emission MUST be **pinned, not merely required to be
  deterministic**. The Edge Cases entry for a route rejected on more than one ground
  obliges the report to be deterministic about "which diagnostics are emitted and in
  what order"; that phrasing presupposes an order without supplying one, so replay
  byte-identity (FR-014) rests on a convention no artifact states. Four rules fix it.
  [US1] [US2]
  - **Cardinality per route: every applicable reason, not the first.** A route that
    fails more than one independent check MUST emit one diagnostic per failed check.
    Emitting only the highest-precedence reason would discard reportable input classes
    and would make the no-safe-route report's "each rejection reason" (FR-029)
    incomplete. This is also the repository's own accumulating precedent —
    `claude_policy_controls.py:2282-2298` collects a breach finding for **every**
    exceeded budget dimension of one record and raises with all of them, rather than
    on the first — and it is the convergent external practice: `google.rpc.BadRequest`
    types `field_violations` as a repeated field describing all violations in a
    request, and RFC 9457's `errors` extension array reports multiple same-category
    problems in one response.
  - **Inter-code order: the FR-005 declaration order.** Within one attempted route,
    diagnostics MUST be emitted in the order the resolution enum declares its members —
    `preferred_model_unavailable`, `effort_unsupported`, `capability_probe_unavailable`,
    `treatment_probe_failed`. The Edge Cases example (effort unsupported *and*
    exact-invocation probe failed) therefore emits `effort_unsupported` then
    `treatment_probe_failed`, and a reviewer can derive that sequence from the
    requirements alone. Declaration order is chosen over the alternative in-tree idiom,
    the alphabetical `sorted(set(reasons))` at `claude_policy_controls.py:2524`, because
    sorting scrambles a precedence that carries meaning and cannot be made structural.
  - **This order is separate from the FR-006 sub-reason order and neither supplies the
    other.** The sub-reason order is *intra-diagnostic*: it selects the single
    `details.sub_reason` value a `preferred_model_unavailable` entry carries. The order
    here is *inter-diagnostic*: it sequences whole entries. Both MUST be structural in
    the simulator (a staged call graph, per FR-006) rather than a comment; conflating
    them would leave the inter-code sequence unpinned while appearing to be covered.
  - **Whole-array order.** `diagnostics` MUST be ordered as three stages: first the
    policy-document violations FR-019c assigns to the pre-walk pass, ordered by the
    declared route position they concern and then by the FR-019 declaration order;
    second, for each `attempted_routes` entry in attempt order, that route's
    diagnostics in the inter-code order above, with `fallback_loop` emitted after the
    last attempted route's entries because it is detected on reaching the revisit;
    third `unqualified_override` if present, and last **exactly one**
    `no_safe_route` entry when the outcome is `no_safe_route`, which MUST be the final
    element of the array.
  - **The outcome value and the diagnostic code are coupled both ways.**
    `no_safe_route` is the one token this contract uses in two roles — a member of the
    `outcome` discriminator (FR-013a) and a member of the resolution enum (FR-005) — and
    the relationship MUST be stated so the two cannot drift apart within one report.
    `outcome` is `no_safe_route` **if and only if** the `diagnostics` array carries
    exactly one entry whose `code` is `no_safe_route`; a `resolved` report MUST carry
    none. Without the biconditional a report could claim `resolved` while carrying a
    terminal failure diagnostic, or claim `no_safe_route` while carrying no remediation
    at all — and it is the `no_safe_route` diagnostic that carries the mandated rollback
    action (FR-012a, FR-029), so its presence is what makes SC-010 reachable.
- **FR-012c**: `severity` and `source` MUST be pinned, because both are required fields
  that enter the serialized bytes FR-014 compares. For `severity` this is a **deliberate
  divergence from the installed runner, not a mirroring of it** — the runner's mechanism
  is caller-determined (`severity` is a keyword parameter defaulting to `"error"`, and
  `plan_layers_diagnostic` takes `code` and `severity` as two *independent* parameters,
  which is exactly the signature you would not write if severity were a function of
  code), and no code-to-severity table exists anywhere in the runner. The divergence is
  justified by a difference in emitter: the runner's emitter is *code*, which needs a
  default, whereas this feature's emitter is a *hand-authored corpus*, where leaving
  severity to the emitter means the corpus author picks freely per case — unfalsifiable
  authoring latitude in a byte-compared corpus. [US1] [US2]
  - **`severity` is a function of `code`.** Each code MUST carry one fixed severity,
    fixed once in the code-to-severity table in `data-model.md` §3 and asserted by a
    single test over every emitted diagnostic. The four route-rejection codes are
    `warning` — a rejected route is not itself a failure, since the walk may still
    resolve on a later fallback — and `unqualified_override` is `warning` because
    dispatch proceeds under it. `no_safe_route` and the four policy-authoring
    violations are `error`. This makes `error` a usable threshold: its presence means
    the policy is unusable as written, while a report carrying only `warning` entries
    resolved despite them. External practice on this is genuinely **divided** —
    LSP 3.17 types `severity` as an optional per-`Diagnostic` field and SARIF lets a
    per-result `level` override the rule's `defaultConfiguration.level`, whereas ESLint
    fixes severity per rule ID with no per-occurrence override (an open request to
    change that, `eslint/eslint#16040`, confirms the limitation is current practice
    rather than an oversight). This feature takes the rule-level pole deliberately:
    every diagnostic here is hand-pinned in a byte-compared corpus, so a
    context-varying severity would be unfalsifiable authoring latitude rather than
    expressiveness. No in-tree precedent decided it — no schema under
    `layer6-efficiency/` binds a code to a severity, and the runner merely defaults the
    keyword to `error` (`envelope.py:43-47`) while its validator checks set membership
    only (`gates/release.py:823`).
    **The external split is not the deciding input, because the standards answer a
    different question** — runtime severity derivation for tools emitting *unbounded*
    findings, versus this feature's authoring constraint on a *bounded, hand-pinned*
    corpus. LSP in particular does not support the occurrence-level reading: it carries
    no rule catalog on the wire, so its omission fallback is a fixed constant rather
    than a rule default, leaving it silent on this question. SARIF's per-result `level`
    is interchange-superset accommodation, and its documented variation axis is
    per-*run* configuration for audit and reproducibility, not per-occurrence semantics.
    The decisive grounds are internal: this feature already emits **exactly one terminal
    diagnostic, always last**, and already carries a **dedicated gate field**
    (`release_claim_eligible`), so every fact a per-occurrence severity could express is
    already carried structurally — and a second channel could contradict the first. That
    also settles the hard case: `unqualified_override` is `warning` in *both*
    configurations, including when it coexists with `no_safe_route`, because the
    consequence travels on `release_claim_eligible` and the terminal `no_safe_route`
    entry already supplies the report's `error`. This feature is SARIF-shaped
    (descriptive severity plus a separate gate), not ESLint-shaped (severity *is* the
    gate).
  - **`source` is a single constant.** Every diagnostic this simulator emits MUST carry
    `source` as the literal `route-fallback-simulator`, constrained with `const` in both
    diagnostic `$defs`. Left as an open `minLength: 1` string it is an unpinned byte in
    every diagnostic of every case. The runner mirrors this shape exactly — it hardcodes
    one literal per producing module (`envelope.py:55`) and its own `is_diagnostic`
    predicate keys off that value (`envelope.py:70`) — so a `const` here encodes in the
    schema what the runner enforces in code. The value is capability-named, never
    spec-ID-named, consistent with FR-032.
- **FR-013**: The resolution report MUST record, for each resolved agent, the
  effective dispatch tuple that resolution selected, so consumers can read the
  outcome without re-deriving it from the attempt list. [US1]
- **FR-013a**: The resolution report MUST be a **single** schema shape discriminated by
  a required `outcome` field whose closed values are `resolved` and `no_safe_route`,
  with conditional requiredness expressed as `allOf` + `if`/`then` carrying `required`
  and `not: {required: [...]}` — the idiom the committed Layer 6 Claude contracts
  already use. It MUST NOT be expressed as a root-level `oneOf` or as two separate
  report schemas. Root `oneOf` is reserved in this directory for documents that are
  unions of distinct *record classes*, and a partition by outcome is **impossible**
  here: the FR-024 override path produces a `no_safe_route` report that still carries
  `effective_dispatch_tuple`, so a success variant and a failure variant do not
  partition the space. [US1]
  - Required in **both** outcomes: `schema_version`, `agent`, `outcome`,
    `attempted_routes` (in attempt order; empty if and only if the policy was rejected
    before the walk started — FR-019c), `diagnostics` (present, possibly empty —
    FR-011 requires a clean success to emit none; ordered by FR-012b), `budgets`
    (declared caps plus actual counts, counted per FR-026a), `release_claim_eligible`
    (derived per FR-024a), `optional_helper` (valued per FR-025a).
  - `effective_dispatch_tuple` is required when `outcome` is `resolved`, **and
    additionally** required when an override is in force.
  - `unresolved_agent` is required when `outcome` is `no_safe_route` and **forbidden**
    when `outcome` is `resolved`.
  - `override` is optional, present only when the synthetic environment carries one,
    and carries the would-have-been qualified resolution FR-024 requires.

#### Determinism, corpus, and contract placement (User Story 1)

- **FR-014**: Each scenario corpus case MUST pin its full expected resolution
  report, and the test MUST assert that two successive simulator runs over
  identical inputs are byte-identical to each other and byte-identical to the
  pinned report under canonical JSON serialization. [US1]
- **FR-014a**: "Canonical JSON serialization" MUST resolve to a single named in-tree
  function rather than to a restated convention. Every unpinned dimension admits two
  conforming implementations that disagree byte-for-byte, which would make FR-014
  unfalsifiable. The serializer is `canonical_json` from the Layer 6
  successor-freeze library — `sort_keys=True`, `separators=(",", ":")`,
  `ensure_ascii=False`, `allow_nan=False` — which pins key order, whitespace,
  unicode escaping, and non-finite rejection in one place. Three further dimensions
  MUST hold, none of which that call signature settles: [US1]
  - **No trailing newline.** The serialized report ends at its closing brace. This
    MUST be stated rather than assumed, because the dimension is genuinely divergent
    in-tree: the repository carries eight `canonical_json` definitions and three of
    them append a newline. A silent mismatch here is the most likely way FR-014
    fails.
  - **One serializer, not two.** The simulator and the pinning test MUST reach the
    same function by import. The test MUST assert over the string the simulator's own
    `serialize_report` returns, and MUST NOT re-declare a local `canonical_json` —
    which is the dominant habit in the unit tree, where all six existing occurrences
    re-declare it and two of those six append a newline. Re-serializing the parsed
    report on both sides of the comparison would *cancel* a serializer discrepancy
    rather than catch it, leaving a green test over a simulator whose real output
    differs.
  - **No floating-point field.** Every numeric field in the report is an integer —
    the declared budget caps and the actual counts — so `repr`-dependent float
    rendering is unreachable rather than merely unlikely. `allow_nan=False` rejects
    non-finite values but does not pin float formatting, so the absence of float
    fields is recorded as an invariant instead of a hope.
- **FR-015**: The scenario corpus MUST be a single self-contained file under the
  Layer 6 efficiency fallback fixtures directory, organized as a list of cases
  where each case bundles its own policy, synthetic snapshot, overrides,
  declared budgets, and expected report, so each case is readable and replayable
  in isolation. [US1]
  The corpus MUST remain a single file across both slices. Slice 1 commits the User
  Story 1 cases; slice 2 appends the User Story 2 cases at the tail of `cases[]` and
  MUST NOT alter any case slice 1 committed. Case order is **declaration order, not
  sorted** — matching the existing pinned-replay precedent — so an appended case
  never reorders an existing one and never perturbs an existing case's pinned bytes.
  [US1] [US2]
- **FR-015a**: Case identity and self-containment MUST be **mechanically asserted**,
  not left to prose. FR-033b's append-only seam rule and SC-007's read-one-case
  guarantee both depend on these properties, and the corpus has no schema of its own
  to enforce them — FR-016 permits exactly three schema documents and none validates
  the corpus envelope. Slice 1's test MUST therefore assert, over the whole `cases[]`
  array: [US1] [US2]
  - **`case_id` uniqueness** — the count of distinct `case_id` values equals the
    count of cases. Nothing in the repository asserts this today for any fixture
    corpus, so it is a new obligation rather than an inherited one.
  - **`case_id` non-emptiness and shape** — each is a non-empty string, so a case
    cannot be silently keyed by `null` or `""`.
  - **Per-case self-containment** — every case carries its own `policy`, `snapshot`,
    `overrides` (explicitly `null` when the case declares none, never absent), and
    `expected_report`. Declared budgets are reached through `policy` per FR-003.
  - **No cross-case reference** — no case's payload names another case's `case_id`,
    so a case can be read and replayed in isolation as SC-007 requires.

  **Cross-slice stability is deliberately *not* claimed as mechanically enforced.**
  Uniqueness and self-containment above are checkable from a single committed state;
  "slice 2 altered no slice-1 case" is a statement about two states and is enforced by
  FR-033b plus diff review, not by any assertion. The replay test cannot substitute:
  if slice 2 re-pinned a slice-1 case's inputs *and* its expected report together, the
  test would still pass because both sides of the comparison moved. Recording which
  half is mechanical and which is review-borne prevents a reviewer from trusting a
  guarantee that does not exist.
- **FR-016**: New JSON Schema contracts MUST land platform-scoped in the Layer 6
  efficiency Claude contracts directory and MUST match the existing schema style
  there (JSON Schema draft 2020-12 with the established `$id` convention). No
  member may be added to the shared byte-identical contracts directory. [US1]
  The three contracts MUST be three separate documents — `route-policy.schema.json`,
  `environment-snapshot-projection.schema.json`, and
  `route-resolution-report.schema.json` — each carrying an
  `https://racecraft.dev/schemas/car-005/<name>.schema.json` `$id`, and **no document
  may use a `$ref` that leaves its own `#/$defs/`**; cross-document `$ref` resolution
  is prohibited in this contracts directory. Filenames MUST be capability-named, never
  spec-ID-named. All three land in slice 1. No fourth shared-definitions schema may be
  introduced: `digest`- and `binding`-style helpers are re-declared locally in all
  eleven existing documents, and there is no cross-file `$ref` anywhere in the
  directory. [US1]
- **FR-016a**: Enums MUST be declared **inline at their point of use**, not as bare
  named `$defs` members. No bare-enum `$defs` exists anywhere in this contracts
  directory; every enum in all eleven documents sits at either
  `/properties/<field>/enum` or `/$defs/<objectShape>/properties/<field>/enum`.
  Accordingly the resolution report MUST express its two closed enums as **two
  diagnostic-entry `$defs`, each carrying its own inline `code` enum**, unioned by a
  `oneOf` where the report's diagnostics array is declared —
  `$defs/resolutionDiagnostic/properties/code/enum` and
  `$defs/policyViolationDiagnostic/properties/code/enum`. This reuses the
  `oneOf`-over-sibling-variants idiom the directory already licenses for multi-shape
  documents, and it gives FR-017a a stable JSON pointer to exactly the five
  route-resolution codes. [US1]
- **FR-017**: A structural test MUST enforce the resolution enum against the
  roadmaps in two distinct assertions, so drift on either platform fails
  visibly rather than silently stranding the Codex twin: [US1]
  - **FR-017a**: The test MUST assert exact set equality between the committed
    resolution-report schema's route-resolution enum and the five codes the
    **Claude** routing roadmap pins. Drift in either direction MUST fail — a
    missing member and an extra member both fail. The Claude roadmap is
    authoritative for this platform's enum. The test MUST read the enum **live** from
    the committed schema by JSON pointer
    (`$defs/resolutionDiagnostic/properties/code/enum`) and MUST NOT transcribe its
    members into the test file — a test that restated the enum would absorb the very
    drift it exists to catch.
  - **FR-017b**: The test MUST pin the known cross-platform divergence as data
    rather than prose: the four shared members (`preferred_model_unavailable`,
    `effort_unsupported`, `treatment_probe_failed`, `no_safe_route`) are
    byte-identical across both routing roadmaps, and the third member is a
    recorded, intentional divergence — `capability_probe_unavailable` on Claude
    versus `capability_discovery_unavailable` on Codex. An unnoticed change to
    either side MUST fail the test. This feature MUST NOT edit the Codex
    roadmap or any Codex-side artifact.
  - **FR-017c**: The recorded third-member divergence is a **permanent intentional
    platform difference**, not deferred drift. Evidence that it is semantic rather
    than cosmetic: each roadmap's *scenario* name matches its own *code* name — Claude
    mandates a "probe unavailable" scenario and pins `capability_probe_unavailable`,
    while Codex mandates a "discovery unavailable" scenario and pins
    `capability_discovery_unavailable`; Codex treats discovery and probing as distinct
    concepts, mandating "discovery unavailable" alongside a *separate* exact-invocation
    availability probe and treatment probe, where Claude has no such split; the Codex
    term recurs consistently across its own scope and its downstream live-UAT scope,
    which a typo would not survive; and Codex carries an approved/unapproved
    service-reroute layer with no Claude analogue. Reconciliation is therefore **not**
    planned — it would force one platform to adopt a term that misdescribes its own
    mechanism, for zero operational gain, and a synchronized two-platform amendment is
    the CAR-012 situation this program exists to avoid. The single review trigger that
    would reopen the question is a future decision to promote a resolution-enum-bearing
    schema into the shared byte-identical contracts directory. No Codex-side artifact
    is edited by this feature; FR-017b's data pinning remains the enforcement
    mechanism regardless of disposition.
- **FR-018**: All fixture policies MUST draw their agent names from a small
  synthetic cast of three role classes — a required executor, a bounded analyst, and
  an optional helper — and MUST NOT name any real shipped agent. [US1]
  - **Every fixture agent name MUST carry the `fixture-` prefix**, giving the cast
    `fixture-required-executor`, `fixture-bounded-analyst`, and
    `fixture-optional-helper`. This is the positive form of the rule and it is what
    the corpus is asserted against; the design concept fixed the `fixture-*` cast at
    Q5 and CAR-002 set the precedent with its `PROBE_AGENT_NAME = "car002-probe"`
    (`claude_capabilities.py:450`). The prefix rule is required in addition to the
    negative one because the negative one alone is **not stable**: the shipped roster
    is eleven agent definitions under `speckit-pro/agents/` today, and a twelfth
    (`autopilot-fast-helper`) is net-new in CAR-010, so a blocklist keyed to a
    snapshot of the roster silently stops covering names added after it was written.
    A prefix test cannot go stale that way, and it is also what makes the design
    concept's stated purpose — that simulation output be impossible to mistake for a
    shipped-route claim in a grep result or a review — actually hold.
  - **The negative assertion MUST derive its roster live** rather than transcribing
    agent names into the test, for the same reason FR-017a reads the resolution enum
    live: a transcribed roster absorbs the drift it exists to catch.
  "Cast" describes the vocabulary the corpus draws from, **not** the number of agents
  one policy names. A policy names exactly one agent as its subject (FR-003) and MAY
  additionally declare one optional helper (FR-025b); the third role class appears as
  the subject of its own cases. Stating the distinction is what reconciles this
  requirement's plural phrasing with a policy contract rooted on a single agent
  identity — a reading under which every policy had to name all three was the earlier
  ambiguity here. Each of the three classes MUST be the subject or declared helper of
  at least one corpus case, so the sufficiency claim in Assumptions is checkable
  against the case allocation rather than asserted.

#### Structural policy rejections (User Story 2)

- **FR-019**: The system MUST define a second closed policy-violation reason-code
  enum whose members are exactly `fallback_loop`, `unqualified_adjacent_model`,
  `generic_agent_substitution`, `silent_inherit_materialization`, and
  `unqualified_override`. [US2]
  This enum MUST be declared in **slice 1**, in `route-resolution-report.schema.json`,
  alongside the route-resolution enum — even though no slice-1 corpus case can emit a
  policy-violation code. Declaring a closed vocabulary in full while most members are
  unexercised is the established practice in this contracts directory, not a review
  smell: `score-bundle.schema.json:88-89` declares a 12-member `failure_plane` and a
  36-member `failure_code` enum, of which at most 4 members are exercised by any
  shipped fixture. Declaring both enums in slice 1 also means slice 2 modifies **no
  schema file at all** — strictly stronger than FR-033b's append-only rule — and it
  is what makes FR-012 (tagged [US1]) fully satisfiable by the slice-1 contract, since
  FR-012 requires `code` to be drawn from *either* of this feature's two closed enums.
  It MUST NOT be a separate schema document: cross-document `$ref` resolution is
  prohibited here (FR-016), so a separate document could only be referenced illegally,
  and a second document would force the enum to be restated — the exact drift the
  read-enums-live discipline exists to prevent. [US1]
  The five members are exactly sufficient — no sixth is needed. The roadmap's four
  named rejections map one-to-one onto the first four members, and
  `unqualified_override` covers the override condition. Three near-misses resolve
  without a new member: budget exhaustion is **bounded, not rejected**, and terminates
  into `no_safe_route` with FR-026 counters; an out-of-range *declared* budget is an
  FR-027 schema-validation failure, so the fixture never loads and no code is emitted;
  and helper-unavailability is a structured field, not a diagnostic (FR-025). The Codex
  roadmap's rejection list is strictly longer — it adds partial required-agent
  installation and fallback changes to instructions, tools, skills, MCP, sandbox,
  mutation, or output contracts — but those have no Claude analogue, and FR-017a makes
  the Claude roadmap authoritative for this platform's vocabulary. Importing them would
  be enum drift, not parity. [US2]
- **FR-019a**: **Slice 1** MUST ship a negative-validation test asserting that a
  diagnostic entry whose `code` falls outside **both** closed enums fails schema
  validation. The test MUST construct the instance and schema **inline** and MUST NOT
  require a corpus case. This is the requirement that makes declaring the
  policy-violation enum in slice 1 safe: without it, slice 1 would ship a closed
  vocabulary whose closure is unproven within its own diff, and SC-003 would genuinely
  be unmet for that enum until slice 2. It is also the repository's established
  technique — an existing Layer 4 test class proves schema-engine keyword coverage for
  keywords that no shipped fixture exercises, constructing instances inline for exactly
  this reason. Note that SC-003 is a **negative** property ("an unrecognized code fails
  validation rather than passing through"), so it is provable with zero corpus cases;
  the positive-emission obligation belongs to SC-001, which is satisfied at feature
  completion rather than per-slice. [US1]
- **FR-019b**: **Slice 1** MUST additionally assert **exact set equality** on the
  policy-violation enum, read live by JSON pointer
  (`$defs/policyViolationDiagnostic/properties/code/enum`), against the five members
  FR-019 fixes. Drift MUST fail in both directions — a sixth member and a dropped
  member both fail. FR-019a alone is insufficient: proving that one out-of-vocabulary
  code fails validation shows the field is constrained, not that it is constrained to
  *these five*. Without FR-019b a sixth member could be added, or one of the five
  silently removed, and no test in the suite would fail — whereas the
  route-resolution enum already has exactly this guarantee from FR-017a, so the two
  closed vocabularies would otherwise ship with unequal protection. [US1]
  Unlike FR-017a, this test **does** declare its five expected members in the test
  file, and that is correct rather than a violation of the read-live discipline. The
  two cases are inverses. FR-017a compares two independently committed artifacts —
  the schema and the roadmap — so transcribing either one collapses two witnesses
  into one and absorbs the drift the test exists to catch. The policy-violation
  vocabulary has **no** independent committed authority: the roadmap names its four
  rejections in prose (`Reject fallback loops, unqualified adjacent models,
  generic-agent substitution, and silent inherit materialization`) and never as
  code tokens, and the fifth member `unqualified_override` is this spec's own
  addition. The schema is the only artifact carrying the tokens, so a test-side
  literal is the second witness, and it is what makes drift detectable at all. [US1]
- **FR-019c**: The **timing** of structural policy validation relative to the route
  walk, and the **report a structural rejection produces**, MUST both be stated as
  requirements. Today neither is: "pre-pass" appears only in FR-033a's slice-allocation
  cell and in FR-033d's one-module justification, both of which are statements about
  module structure rather than evaluation order, and FR-020 through FR-023 impose no
  ordering at all. [US2]
  - **The defects partition; they are not uniformly pre-walk.** Three are properties of
    the policy **document**, decidable by reading the declared routes with no walk
    state: `unqualified_adjacent_model`, `generic_agent_substitution`, and
    `silent_inherit_materialization`. These MUST be evaluated in a pass that completes
    **before the first route is attempted**, and when that pass emits any diagnostic the
    walk MUST NOT start. `fallback_loop` is **not** in that pass: FR-020 defines it
    against a route "already-attempted" and requires the walk to "terminate without
    repeating that route", and FR-001 states its detection "needs the walk state that
    this module already owns". It is therefore detected during the walk, at the point
    the revisit is reached. Recording the partition is what reconciles those two
    statements with the pre-pass framing, which is accurate for three codes and was
    over-generalised to four.
  - **A pre-walk rejection records no attempts.** `attempted_routes` MUST be **empty**
    in a report produced by the pre-walk pass, and empty in no other report — the array
    is empty **if and only if** the pre-walk pass rejected the policy. Recording a route
    as attempted when it was not would misreport the walk, so the array's lower bound
    MUST admit zero. This is a deliberate departure from the directory's one existing
    attempt-array precedent, `contracts/treatment-record.schema.json:940-945`, which
    declares `attempted_route_ids` with `minItems: 1`; the biconditional above replaces
    the guarantee that bound was providing, and it must be stated rather than implied,
    because this directory's established habit is to make "a stage that was not reached"
    explicit rather than absent (`contracts-claude/analysis-decision.schema.json:57,71`
    records `not_evaluated` for an unreached gate, with the description "A gate that was
    not reached records not_evaluated rather than being omitted").
  - **The report is a valid FR-013a report, not an under-specified one.** For a pre-walk
    rejection: `outcome` is `no_safe_route` — the only member of the closed discriminator
    that a rejected policy can take, and `resolved` is unreachable because no route was
    selected; `unresolved_agent` is the policy's own agent name, satisfying FR-013a's
    conditional branch; `effective_dispatch_tuple` is absent unless an override is in
    force (FR-024a); `diagnostics` carries the violations in FR-012b's order plus the
    terminal `no_safe_route` entry; `budgets` carries the declared caps with all three
    actual counts at `0`, since nothing was probed, retried, or walked;
    `optional_helper` takes its not-consulted form (FR-025a); and
    `release_claim_eligible` is `false` (FR-024a).
  - **`unqualified_override` is not part of this pass.** It shares the policy-violation
    enum but is an environment condition read from the overrides input, not a defect of
    the policy document, so it is evaluated where FR-024 places it and never suppresses
    the walk.
- **FR-020**: A policy whose fallback chain revisits an already-attempted route
  MUST be rejected with `fallback_loop`, and the walk MUST terminate without
  repeating that route. [US2]
- **FR-021**: A policy naming a fallback that is adjacent to a qualified route
  but not itself qualified MUST be rejected with `unqualified_adjacent_model`,
  and that fallback MUST never be selected. [US2]
- **FR-022**: A policy substituting a generic agent for a named synthetic agent
  MUST be rejected with `generic_agent_substitution`. [US2]
- **FR-023**: A policy route omitting an explicit model or effort such that the
  value would be materialized by inheritance MUST be rejected with
  `silent_inherit_materialization`. [US2]

#### Override and helper paths (User Story 2)

- **FR-024**: When the synthetic environment carries an unqualified subagent-model
  override, the report MUST record the override as the effective dispatch tuple,
  emit an `unqualified_override` diagnostic, mark the environment as excluded
  from release claims, and additionally record the qualified resolution that
  would have applied without the override. [US2]
- **FR-024a**: Four consequences of combining FR-024 with FR-013a MUST be stated —
  three because each is otherwise derivable only by inference and each changes reported
  bytes, and a fourth because the program's position on a neighbouring condition would
  otherwise read as a missing disqualifier. [US2]
  - **`outcome` follows the qualified walk, never the override.** An override MUST NOT
    turn a `no_safe_route` outcome into `resolved`. FR-013a already relies on this — it
    justifies rejecting a root `oneOf` by observing that "the FR-024 override path
    produces a `no_safe_route` report that still carries `effective_dispatch_tuple`" —
    but never states it as a rule, leaving open the opposite reading in which an override
    is always dispatchable and therefore always resolves. `outcome` describes what
    qualified resolution achieved; `effective_dispatch_tuple` describes what will
    actually dispatch. The two disagree exactly when an override is in force, which is
    the condition that makes the environment ineligible for release claims.
  - **`release_claim_eligible` has a derivation rule for every report, not only the
    override case.** It is required in both outcomes, yet only the override path fixes
    it. Following this directory's established asymmetry — the closest analogue,
    `qualification_eligible`, is schema-forced to `false` under a named condition
    (`contracts-claude/experiment-assignment.schema.json:52-56`) with no matching
    true-forcing branch, and its companion reason vocabulary carries fourteen
    disqualifying members against one residual `none`
    (`contracts-claude/analysis-decision.schema.json:79-95`) — the rule is written as a
    closed list of disqualifiers with `true` as the residual.
    `release_claim_eligible` MUST be `false` when **any** of the following holds: an
    override is in force; `outcome` is `no_safe_route`; or the report carries any
    policy-violation diagnostic. It is `true` only when none holds. A no-safe-route
    report therefore reads `false` even with no override present — claiming a release on
    an environment where a required agent does not resolve is precisely what the
    rollback remediation exists to prevent.
  - **The would-have-been tuple is omitted, not `null`, when there is nothing to
    record.** `override.would_have_been` always carries its own `outcome`; its
    `effective_dispatch_tuple` member MUST be **absent** when no qualified route
    resolved, and MUST NOT be present as `null`. This has to be stated rather than
    deduced from canonical serialization: RFC 8785 canonicalizes an explicit `null` and
    an omitted member equally well and is silent on the choice by scope, so byte
    determinism does not decide it — only a stated rule does. Omission is chosen because
    it is the report's own established idiom (FR-013a expresses every conditional member
    by presence and absence, forbidding `unresolved_agent` outright on the `resolved`
    branch) and because omit-by-default is the external default too, presence being
    tracked separately only where the distinction is load-bearing (Google AIP-149).
    This deliberately differs from FR-015a's rule that a case's `overrides` be
    "explicitly `null` when the case declares none, never absent", and the difference is
    not an inconsistency: the corpus envelope has **no schema** (FR-016 permits exactly
    three documents, none validating it), so there an explicit `null` is the only way to
    distinguish a declared-empty case from a malformed one, whereas the report's schema
    expresses that distinction with conditional requiredness.
  - **A platform route change or an alias re-point is *not* a disqualifier, and the
    silence on that MUST be replaced by a decision.** The program's position on the
    same condition is that a route change "marks the run non-scorable for the
    requested route" (`claude-agent-routing-technical-roadmap.md:432-435`), which
    reads at first like a fourth disqualifier. It is not, because the two answer
    different questions at different scopes. CAR-002's non-scorability is
    **route-scoped** and concerns whether a *measured outcome* can be attributed to
    the requested tuple; `release_claim_eligible` is **report-scoped** and concerns
    whether this environment resolved its agent to a qualified route. A report whose
    preferred route was rejected for `alias_repointed` or `platform_route_changed`
    and which then resolved on a declared qualified fallback is
    `release_claim_eligible: true`, deliberately: the route that will dispatch is
    qualified and its model was present in the snapshot. The route-scoped fact is not
    lost — it is carried by that route's `attempted_routes` entry with `disposition:
    rejected` and by the sub-reason in its diagnostic, which is exactly the
    "recorded separately from resolver fallback" CAR-002 asks for. Recording this as
    a decision is what distinguishes it from an omission from the disqualifier list.
- **FR-024b**: The override's **runtime referent** MUST be named and its documented
  behaviour MUST be matched, because FR-024 exists to simulate honestly and a fixture
  that pins behaviour the runtime does not have is worse than no fixture. Today the
  requirement says only "an unqualified subagent-model override", naming no mechanism,
  defining no qualification test, and asserting an unconditional effect. [US2]
  - **The mechanism is `CLAUDE_CODE_SUBAGENT_MODEL`.** The roadmap names it in this
    feature's own scope ("an unqualified `CLAUDE_CODE_SUBAGENT_MODEL` override",
    `claude-agent-routing-technical-roadmap.md:602-603`) and this spec dropped the name.
    The override record's `source` field MUST therefore be pinned with `const` to that
    identifier rather than left an open string, for the same reason FR-012c pins
    `source` on diagnostics: an unpinned required field is an unpinned byte in every
    case that carries it, and an override whose mechanism is anonymous cannot be
    checked against a documented behaviour at all.
  - **Its documented precedence is what makes "wins at dispatch" true.** The
    documented subagent model-resolution order places the environment variable
    **first**, above the per-invocation model parameter, above the subagent
    definition's `model` frontmatter, and above the main conversation's model. The
    repository's own dated extract records the same fact
    (`docs/ai/research/claude-agent-route-candidates.md:619-624`, `RES-1`/`RES-2`:
    "Overrides the per-invocation `model` parameter and the subagent definition's
    `model` frontmatter"). FR-024's effective-dispatch-tuple rule is grounded in that
    ordering and MUST cite it rather than assert it.
  - **The override is conditional, and this is the correction that matters.** The
    documented runtime checks the environment variable, the per-invocation parameter,
    and frontmatter against the organization's model allowlist, and **skips a value
    that resolves to an excluded model**, running the subagent on the inherited model
    instead. FR-024 as written asserts the override becomes the effective dispatch
    tuple unconditionally, which is a stronger claim than the runtime supports. The
    corrected rule: the override becomes the effective dispatch tuple **only when its
    target passes the allowlist**; when it does not, the override is **skipped** and
    MUST NOT be recorded as effective. The allowlist is an FR-002 projection member
    precisely so this branch is decidable from the snapshot.
  - **What the skipped branch may and may not claim.** It MUST record that the
    override did not take effect and MUST NOT name the model that runs instead: the
    documented fallback target is the *inherited* model, which this projection does
    not carry and MUST NOT gain — a parent-session model is a live-preflight input
    belonging to CAR-006, not to a pure function over a route policy and a snapshot.
    Reading the skip as "resolution resumes at the per-invocation parameter" is
    **inference and MUST NOT be encoded**; the documentation says inherited. So the
    skipped case's honest claim is bounded to the negative. `release_claim_eligible`
    is nevertheless `false` on that branch too, and for a reason independent of
    FR-024a's override disqualifier: the environment carries the interference surface
    *and* the model that dispatches is neither the policy's pinned route nor the
    override's target, so it is the least attributable of the three states.
  - **The allowlist gate is a different gate from this feature's own qualification.**
    Allowlist membership is an organizational configuration; "qualified" is a
    fixture-declared property (see Assumptions). The two are independent, so an
    override can be unqualified yet allowlist-permitted, or qualified yet
    allowlist-excluded. Conflating them would make the two branches indistinguishable.
  - **"Unqualified" MUST be defined rather than assumed.** An override is
    **unqualified** when the tuple it produces matches no route the policy declares
    qualified — which is the test CAR-006 is scoped to perform ("validate the
    resulting tuple for every named agent against qualified routes",
    `claude-agent-routing-technical-roadmap.md:676-677`). Without the predicate the
    corpus case is authored against an undefined term and SC-001's
    unqualified-override family has no falsifiable membership test.
  - **A qualified override is in force too.** FR-024a disqualifies a report when "an
    override is in force" while FR-024's diagnostic is scoped to an *unqualified*
    one, leaving the qualified case unstated. It is resolved in the direction FR-024a
    already took: any override in force sets `release_claim_eligible: false`, because
    the program's rule is that "release claims exclude overridden environments"
    without qualifying which kind. A **qualified** override in force records the
    override as effective and sets the flag `false`, but emits **no**
    `unqualified_override` diagnostic — the diagnostic reports the qualification
    defect, the flag reports the environment. The corpus need not carry a case for it;
    stating the rule is what keeps the two scopes from being read as the same scope.
  - **The effective tuple under an override is a hybrid, and its members MUST be
    attributed.** The variable sets a **model** only; there is no documented
    subagent-effort environment override, and effort is carried by the subagent
    `effort` field (FR-007a). Since the dispatch tuple requires an effort, the
    override cannot supply the whole tuple and "record the override as the effective
    dispatch tuple" is imprecise as written. The rule: under an override in force,
    `effective_dispatch_tuple` carries the override's model — with its `alias` member
    holding the override's own value, which may itself be an alias, since the
    documented variable accepts an alias or a full model ID — and retains the
    **agent** and the **effort** from the route the qualified walk selected, or from
    the preferred route when the walk selected none. Attributing the members is what
    makes the pinned bytes derivable; leaving it implicit invites two conforming
    implementations that disagree on the effort member.
  - **The `inherit` sentinel is excluded, with the reason recorded.** The documented
    variable accepts `inherit` to restore normal model resolution, so it is a **set**
    value that behaves as unset. It is therefore **not** an override and MUST be
    modelled as the no-override state — the case's `overrides` is `null` per FR-015a.
    This is not a free choice: CAR-002's committed unset proof already treats it this
    way and records the caveat that the equivalence is client-version-gated
    (`claude_capabilities.py:725-747`, `inherit_equivalent_to_unset`). Version-gating
    is out of scope here — this simulator has no client-version input by FR-001 — and
    saying so is what stops a reader from expecting a version dimension the
    projection does not carry.
  - **The claims-exclusion consequence follows the program, not only this spec.**
    FR-024a reasons the disqualifier from this report's internals; the external
    warrant is stronger and MUST be cited. CAR-002's exact-treatment replay schema
    binds "env-override proof (`CLAUDE_CODE_SUBAGENT_MODEL` unset)"
    (`claude-agent-routing-technical-roadmap.md:428-431`) — the program's posture for
    a scored run is *proof of unset*, which is strictly stronger than flagging an
    override after the fact. CAR-006 then requires overrides be reported "loudly" with
    "release claims exclude overridden environments" (`:675-678`). This feature is the
    complement of CAR-002's proof: it pins what the report must say when the surface
    CAR-002 proves absent is present instead.
  - **The corpus MUST carry a second override case.** `override-skipped-by-allowlist`
    is appended alongside the existing honored-override case, in slice 2. One case
    cannot cover both branches, and without the second the corpus would pin the
    unconditional behaviour this requirement corrects. [US2]
- **FR-025**: When the optional helper's routes are unavailable, the helper MUST
  NOT be consulted, the report MUST record continuation on the validated
  no-helper path, and required-agent resolution MUST NOT fail as a result. [US2]
  This continuation MUST be recorded as a **structured report field** — an
  `optional_helper` object carrying `consulted: false` and
  `no_helper_path_validated: true` — and **not** as a diagnostic entry. Helper
  unavailability is neither a rejection nor a remediation, so FR-012 does not apply to
  it and neither closed enum gains a member for it. The roadmap frames it as a
  non-event ("the helper is simply not consulted"), and adding a `helper_unavailable`
  member to the policy-violation enum would repeat exactly the objection that kept
  environment conditions out of that enum in the first place: it is an environment
  condition, not a policy-authoring defect, and the enum's meaning would blur.
- **FR-025a**: "Not consulted" MUST be **measurable from the report**, not merely
  asserted by it. `consulted: false` on its own is a boolean the simulator sets about
  its own behaviour: an implementation could probe every helper route and still write
  `false`, satisfying the letter of FR-025 while violating it in substance, and no
  pinned byte would change. Established practice for making a non-invocation claim
  checkable is an instrumented count rather than a flag — `unittest.mock`'s
  `assert_not_called` is backed by an integer `call_count`, and Mockito's
  `verifyNoInteractions` inspects the mock's recorded interaction history — and metrics
  guidance likewise prefers an emitted explicit zero over inferring absence, because an
  absent series and a never-executed path are indistinguishable. Three obligations
  follow. [US2]
  - **An explicit zero.** `optional_helper` MUST carry a required `probe_attempts`
    integer, and it MUST be `0` in every report where `consulted` is `false`. The
    corpus case pins the zero and the test asserts it, so the claim is falsifiable.
  - **The zero is unambiguous.** `optional_helper.probe_attempts` counts probes spent on
    the **helper's** routes only. It is disjoint from `budgets.actual.probe_attempts`,
    which counts the reported agent's own walk (FR-026a). Without the disjointness
    stated, a zero in one counter could be read as covered by a non-zero in the other.
  - **No helper route appears as attempted.** When `consulted` is `false`, no
    `attempted_routes` entry may name a helper route. This is the corroborating
    structural evidence: a counter alone can be wrong in the same direction as the flag,
    whereas the attempt list is the same array the walk builds for every other purpose.

  The field's values MUST also be specified for the other two reachable states, since
  `optional_helper` is required in **every** report and only the unavailable state was
  described. When the policy declares an optional helper whose routes are available and
  it is consulted: `consulted: true`, `no_helper_path_validated: false`,
  `probe_attempts` at least `1`. When the policy declares no optional helper at all:
  `consulted: false`, `no_helper_path_validated: true`, `probe_attempts: 0` — identical
  to the unavailable state, which is acceptable and deliberate rather than a lost
  distinction, because whether a helper exists is a property of the policy and every
  case carries its own policy (FR-015a), so no reader has to infer it from this field.
  Required-agent resolution MUST be unaffected in all three states, which is the second
  half of FR-025 and the half a helper-unavailable case must also pin. [US2]
- **FR-025b**: The route-policy contract MUST provide the member by which a policy
  **declares** its optional helper. Without one, three obligations already written are
  unsatisfiable, and the defect is structural rather than editorial: FR-003 roots a
  policy on a single named agent, so nothing in the contract can express "a required
  agent *and* an optional helper" — which is exactly what the helper-unavailable case
  needs, and exactly what FR-018's "name a small synthetic cast" (a cast, plural)
  already presumes. [US1] [US2]
  - **The three unsatisfiable obligations.** FR-025a distinguishes its three helper
    states by "whether the policy declares an optional helper", a property no policy
    field carries; `optional_helper.probe_attempts` counts probes spent "on the
    **helper's** routes", which are not locatable; and FR-025a's rule that no
    `attempted_routes` entry may name a helper route is uncheckable when no artifact
    says which routes are the helper's. All three are measurability obligations that
    silently degrade to prose without this member.
  - **The member.** The policy root gains an **optional** `optional_helper` object
    carrying its own agent identity (whose `role_class` MUST be the helper class) and
    its own preferred route and ordered fallback routes — the same route shape the
    required agent uses, so no new route vocabulary is introduced. Absent member means
    the policy declares no helper, which is FR-025a's third state. The declared
    budgets stay on the policy root and are **not** duplicated per helper: the helper's
    probe accounting is the separate disjoint counter FR-025a already defines, not a
    second budget set.
  - **What this does not change.** The policy still resolves and reports for **one**
    agent — the root `agent` — so `outcome`, `unresolved_agent`, and
    `effective_dispatch_tuple` remain single-valued and FR-013a is untouched. The
    helper is declared so its routes are identifiable and its non-consultation
    measurable, never so a second resolution report is produced. One case still carries
    one policy and one expected report (FR-015a).
  - **Slice allocation.** The member lands in slice 1 with the rest of the route
    schema, per FR-033b's rule that slice 2 modifies no schema file; only the
    behaviour that reads it is slice 2. This is the same allocation FR-027 already
    uses for the budget maxima and FR-019 for the policy-violation enum.
  - **The sufficiency claim is corrected, not weakened.** Three role classes remain
    sufficient — the fix adds no fourth class and no fourth synthetic agent. What was
    insufficient was the *contract*, which offered one agent slot for a cast of three
    roles. The Assumptions entry is updated accordingly.

#### Budgets, exhaustion, and no-safe-route recovery (User Story 2)

- **FR-026**: Declared probe, retry, and fan-out budgets MUST be treated as hard
  caps that resolution never exceeds, and the report MUST record the actual
  attempt count alongside the declared budget for each capped dimension. [US2]
- **FR-026a**: Each capped dimension MUST have a **defined unit of counting**, a
  **defined exhaustion outcome**, and a way for a consumer to tell **which** budget
  exhausted. None of the three is stated today, which leaves FR-026's "actual attempt
  count" and SC-009's "never exceeds the declared budget" unfalsifiable — two conforming
  implementations could report different counts for the same case and both claim
  compliance. Declaring the unit is directory practice, not an addition to it: every cap
  in `contracts-claude/policy-control-registry.schema.json:670-676` carries a required
  `unit` drawn from a closed enum alongside its `value`, and that document also defines
  retry exhaustion in prose at `:154` — "Exhausting retries means at least one attempt
  failed". [US2]
  - **`probe_attempts`** increments **once per route whose snapshot probe state is
    consulted** — precisely, once per route's **first** consultation, reading
    capability-probe availability and the exact-invocation outcome together as one
    consultation. A route rejected earlier in the inter-code order, before probing is
    reached, adds nothing. The count is therefore checkable against the report itself,
    following the in-tree definition of one attempt as one entry of an enumerable list
    (`claude_policy_controls.py:2236`).
    **"First consultation" rather than "each consultation" is load-bearing, not
    stylistic.** A retry also reaches probe evaluation, so counting every consultation
    here would make a route probed twice yield `probe_attempts: 2` against
    `candidate_routes: 1` — falsifying the asserted `probe_attempts <= candidate_routes`
    invariant — and would make `retries: 1` **unreachable** under
    `max_probe_attempts: 1`, rendering FR-028 unsatisfiable at its declared all-budgets-1
    configuration. Retries are therefore carved out of this counter by construction: this
    counter takes each route's first consultation, `retries` takes every subsequent one.
  - **`retries`** increments **once per re-consultation of a route whose
    exact-invocation probe outcome is `failure`** — that is, every consultation of a route
    *after* its first, which `probe_attempts` already took. A route whose probe outcome is
    `success` or `absent` incurs no retry. The **exclusive** base (re-attempts only, not
    total attempts) is deliberate and doubly grounded: a field named `retries` excludes
    the initial attempt by universal convention, whereas a field named `attempts` includes
    it — and this repository's own frozen registry independently fixes the same direction
    with "exhausting retries means at least one attempt failed". This schema already
    encodes it too: `max_retries` carries `minimum: 0` where both sibling caps carry
    `minimum: 1`, because "no re-attempt" is coherent while "never probe" is not. So
    `max_retries: 1` admits two consultations of one route.
    **Honest framing of what a retry is here.** Re-consulting an *unchanged* snapshot is a
    no-op by construction — a live retry exists because the outcome *might* change, and a
    deterministic outcome derived from a frozen snapshot is exactly the non-retryable
    class real resilience libraries never retry. So this counter is not literally "a
    re-read that might succeed". It is a **declared allowance for the attempts the live
    CAR-006 preflight would make against a real environment**, which this simulator
    exercises deterministically because the fixture pins the outcome. That is the faithful
    degenerate projection of the live unit CAR-006 inherits, and it matches the registry's
    own posture that exhausting retries is "the one outcome the bound execution trace can
    evidence" — a statement about what the record can prove, not about what physically
    happened. Framing it as a literal re-read would be a fiction; this framing is the same
    arithmetic without one.
  - **`candidate_routes`** increments **once per candidate route entered in the walk** —
    the preferred route plus each fallback reached — so `max_candidate_routes` bounds walk
    breadth and equals the length of `attempted_routes` when the walk runs. This gives the
    third dimension a referent it otherwise lacks in a sequential first-match walk: with a
    fallback list longer than `max_candidate_routes - 1`, the walk stops after
    `max_candidate_routes` routes rather than continuing to the end of the list.
    `probe_attempts` is therefore always less than or equal to this count, and the two are
    not redundant.
    **The roadmap phrase is "fan-out"; this field is deliberately not named that.** In
    this contracts directory the token `fan_out` is **already frozen with a different referent** —
    "a declared ceiling on automatically spawned children"
    (`contracts-claude/policy-control-registry.schema.json:547-551`), and set at dispatch
    time at `:143`. The Codex twin roadmap names that same concept "**subagent** fan-out …
    **in the harness**", confirming the program's referent is dispatch breadth enforced by
    the harness, not resolver walk breadth. Reusing the token here would put two referents
    on one name inside one contracts directory — the same second-dialect trap FR-012
    refuses at this spec's own diagnostics boundary. The program's existing unit for
    entered candidates is `candidates`, already a member of the frozen unit enum beside
    `attempts`, so this field follows precedent rather than departing from it. The token
    `fan_out` stays reserved for its harness sense, which is where CAR-006 will need it.
  - **Counting scope.** All three counters are counted **over the reported agent's own
    walk** — never aggregated across corpus cases or across agents. Stating the scope is
    not optional detail: the frozen registry pairs a `counted_over` scope with every
    ceiling precisely so "a run cannot stay inside its bounds by distributing retries …
    across children", and a ceiling without a scope is as unfalsifiable as one without a
    unit. Note the registry's durable rule is **unit + scope + breach outcome**, not
    "every cap carries a `unit`" — two of its own caps (`boundScopeAndBreach.max_retries`,
    `topologyDescriptor.fan_out`) are bare integers carrying scope and breach semantics
    instead.
  - **All three exhaust into `no_safe_route`.** No new terminal code may be introduced —
    FR-005 closes the resolution enum and forbids extension by this feature, and FR-019
    already records that budget exhaustion is "bounded, not rejected" and terminates
    there. That statement currently sits inside an enum-sufficiency argument rather than
    in a requirement, which is why it is restated here as one.
  - **The exhausted classes MUST be identifiable from the report.** Comparing a counter
    to its cap is **not** sufficient on its own: a walk can legitimately reach a cap
    without failing because of it — two probes under `max_probe_attempts: 2` that both
    resolve produce counter-equals-cap on a `resolved` report. The terminal
    `no_safe_route` diagnostic MUST therefore carry `details.exhausted_budget`: an
    **array** whose members are drawn from the closed three-member inline enum
    (`probe_attempts`, `retries`, `candidate_routes`), listing every class whose actual count
    equals its declared cap, ordered by that enum's declaration, with `minItems: 1` and
    `uniqueItems: true`. It is present on that diagnostic and on no other, so its
    presence means "spent to the limit **and** the walk failed", which is exactly the
    conjunction a single counter comparison cannot express.
    **Required only when at least one class is at cap; omitted — not empty — when none
    is**, since `minItems: 1` forbids the empty array. This is a qualification, not a
    weakening: the field's stated meaning is that its presence means "spent to the limit
    and the walk failed", and omission is what preserves that reading. Two cases make the
    qualification necessary rather than hypothetical. A pre-walk structural rejection
    (FR-019c) fixes all three actual counts at `0` while `max_probe_attempts` and
    `max_candidate_routes` carry `minimum: 1`, so its at-cap set is **necessarily** empty. And a
    `no_safe_route` report arising from an empty fallback list can end below every cap.
    Omission is unambiguous because the report already carries both the declared caps and
    the actual counts, from which the empty at-cap set is re-derivable. Note this defect
    is independent of FR-019c's partition — the empty-fallback-list case reaches it too,
    so it required fixing regardless.
    An array rather than a single naming of "the class that terminated the walk" is
    deliberate, and the difference matters. With more than one cap reached — the FR-028
    case declares all three at `1` and reaches all three — deciding which one *caused*
    termination would require a tie-break rule over simulator internals that no
    observable report content can settle: against a static snapshot a further retry
    would return the same outcome, so no budget's exhaustion changes the result and none
    is causally privileged. Recording the at-cap set is a pure function of the counters
    and caps the report already carries, so it is deterministic by construction and
    needs no such rule. This keeps the practice the external shape recommends —
    distinguishing which limit was reached rather than collapsing every limit into one
    undifferentiated terminal state, as Temporal does with `RetryState` on the failure
    and the AWS SDK retry loop does by naming attempts-exhausted and quota-depleted
    separately — while carrying it as a field rather than a distinct code, which is what
    keeps FR-005's closed enum closed.
- **FR-027**: The schema MUST enforce maxima on the declared budget fields, so a
  fixture declaring an out-of-range budget fails validation rather than being
  clamped at run time. **[US1]** — retagged from US2 at Clarify: the budget fields
  themselves are FR-003 (US1, slice 1), and declaring a field's `maximum` is the
  same schema-authoring act as declaring the field. Splitting them would make
  slice 2 reopen a slice-1 schema for a one-keyword change, which FR-033b forbids.
  The *behavioural* half stays in slice 2: FR-026 (simulator enforces the caps and
  reports actual counts) and FR-028 (the exhaustion case).
  The **negative validation proof travels with the constraint into slice 1**, by the
  same reasoning FR-019a applies to enum closure: an out-of-range budget failing
  schema validation is a property of the slice-1 schema, provable the moment that
  schema exists and provable with zero corpus cases. Filing it under "the behavioural
  half" mis-classified it on this requirement's own terms — it proves *validation*
  rejects, which is not behaviour — and would have left slice 1 shipping a ceiling
  whose enforcement is unproven inside its own diff, exactly the condition FR-019a
  exists to prevent for the enums and that FR-033b forbids by requiring slice 1 to be
  complete and passing alone. Slice 1's test therefore constructs an out-of-range
  declared budget **inline**, in the FR-019a manner, and asserts it fails validation;
  it is not a corpus case, because every corpus case must validate. Honest cost of
  this allocation, recorded: slice 1 declares budget constraints it validates but does
  not yet enforce behaviourally. That is contained inside a contract FR-003 mandates for
  slice 1 regardless, which is why it is the lesser evil against making slice 2 reopen
  a slice-1 schema for a one-keyword change. The co-location itself is universal in
  this directory — every numeric constraint shares the object literal with its field's
  `type`, with zero counterexamples. Recorded caveat: bounding a `max_*` budget field
  from **above** with `maximum` has no exact precedent here (the existing budget
  precedent bounds such fields from below with `minimum`, because there the field's
  value *is* the ceiling), so the keyword choice is this feature's own decision even
  though its placement follows convention.
- **FR-028**: The corpus MUST include a budget-exhaustion case proving the cap
  with a declared budget of one. [US2]
  That case MUST exhaust the **retry** budget specifically, and MUST declare all three
  budgets at `1` while pinning all three actual counts. Naming the class matters because
  the roadmap lists "Prove retry exhaustion" as its own obligation
  (`docs/ai/specs/claude-agent-routing-technical-roadmap.md:624`) while this requirement
  says only "a budget", and User Story 2's acceptance scenario 7 says "a probe or retry
  budget of one" — a disjunction a case could satisfy by exhausting probes and never
  touching a retry, leaving the roadmap's named obligation unproven. Fixing the
  retry budget to bind closes that. Declaring the other two caps at `1` in the same case
  proves they are respected without adding a case: the report pins `probe_attempts` and
  `candidate_routes` against their caps too, and `details.exhausted_budget` lists all three
  classes, so `retries` is provably among the budgets spent to their limit on a failing
  report (FR-026a). The case's mechanics are fixed so this is reachable: the preferred
  route's exact-invocation outcome is `failure`, the single permitted retry re-consults
  it and returns the same `failure`, and no further retry may be taken — which is what
  retry exhaustion means against a static snapshot. All three declared values satisfy the
  schema bounds in `data-model.md` §1 (`max_retries` `minimum: 0`, the other two
  `minimum: 1`), so the case validates. Recorded honestly: no case makes probe-attempt or
  candidate-route exhaustion the *sole* at-cap class, which is acceptable for the same reason
  FR-019 accepts declaring unexercised enum members — one shared cap check governs all
  three dimensions, so separate cases would re-prove the same code path under a different
  field name. [US2]
- **FR-029**: When the preferred route and every declared fallback are rejected,
  the report MUST be report-only, naming the unresolved agent, every attempted
  route, each rejection reason, and remediation whose `actions` include the FR-012a
  member `Roll back to the previous plugin release.` **verbatim**. The simulator MUST
  NOT write or mutate any shipped agent file. [US2]
- **FR-029a**: FR-029's obligations attach to the **outcome**, not to its stated
  precondition, and its two arrays MUST be **joinable** rather than merely co-present.
  [US2]

  **Outcome-attached, not precondition-attached.** FR-029 opens "When the preferred route
  and every declared fallback are rejected", which FR-026a's candidate-route cap now makes
  narrower than the set of reports that need it: a walk truncated at `max_candidate_routes` ends
  with routes that were never reached and therefore never rejected, yet still terminates
  in `no_safe_route`. Every obligation FR-029 imposes — naming the unresolved agent,
  every attempted route, each rejection reason, and remediation carrying the verbatim
  rollback action — MUST therefore apply to **any** report whose `outcome` is
  `no_safe_route`, however the walk ended: every declared fallback rejected, an empty
  fallback list, a budget cap reached, or a pre-walk structural rejection (FR-019c). This
  keeps FR-012a's mandated rollback action universal on that code, which is what SC-010
  depends on, and removes the reading in which a truncated walk escapes the remediation
  requirement on a technicality.

  **Joinable, not merely co-present.** As written, a consumer reading a no-safe-route report is given two
  arrays and no key between them, so the association is positional — and position is not
  a key here, because FR-012b emits a variable number of diagnostics per route, so the
  arrays are not the same length and cannot be zipped. Every diagnostic that concerns a
  specific route MUST therefore carry `details.route_id`: the four route-rejection codes,
  and `fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`, and
  `silent_inherit_materialization`. For a code emitted during the walk the value MUST
  match an `attempted_routes` entry's `route_id`; for a pre-walk violation (FR-019c) it
  names the **declared** route, which by construction was never attempted. `route_id` is
  already the identity the policy schema assigns for exactly this purpose — it is how a
  `fallback_loop` revisit is recognised — so this reuses a key rather than adding one.
  The composition of the report is fixed by the same requirement: the per-route rejection
  diagnostics carry their own single code-specific action, and the rollback action appears
  **only** on the terminal `no_safe_route` entry, which also carries the summary
  remediation. Repeating the rollback on every rejection entry would inflate each entry's
  `actions` array toward the `maxItems: 3` truncation boundary for no added information;
  the code-to-action mapping in `data-model.md` §3 already allocates it to
  `no_safe_route` alone, and this requirement is what makes that allocation binding
  rather than advisory. [US2]

#### Repository and delivery constraints (both stories)

- **FR-030**: The feature MUST be repository-only: zero production files, no
  plugin runtime, payload, or shipped-default change, and all authored code on
  Python 3.11+ standard library with no new Bash or `jq` dependency. [US1] [US2]
- **FR-031**: The feature MUST be additive: no frozen CAR-002, CAR-003, or
  CAR-004 schema or fixture may be edited. [US1] [US2]
- **FR-032**: New scripts and tests MUST use durable capability-based file names
  never coupled to the spec ID, and every new test MUST be registered in the
  test suite manifest. [US1] [US2]
  This is **mechanically enforced**, not merely a convention: an existing layout test
  checks durable naming, and `car` is a live spec family because the feature directory
  is `specs/car-005-...`. Accordingly **no authored script stem and no test method name**
  may contain `car-005`. Schema `$id` values MAY retain `car-005`, because the check
  inspects path stems rather than file contents — and `car-003`/`car-004` already appear
  in every existing `$id` in this directory.
- **FR-032a**: Adding documents to `contracts-claude/` opts them into a pre-existing
  Layer 4 test that asserts every document in that directory uses only JSON Schema
  keywords the shared validation engine implements. Every keyword this feature needs —
  `oneOf`, `allOf`/`if`/`then`/`not`, `minItems`/`maxItems`, `maximum`, and `const` —
  MUST be within that supported set. This was verified during planning; it is recorded
  here so a later change cannot introduce an unsupported keyword unknowingly. `const`
  is listed explicitly because FR-012c now relies on it to pin `source`, a second use
  beyond the `schema_version` pin every document already carries; the engine implements
  it (`claude_policy_controls.py:332`). [US1]
- **FR-033**: The feature MUST be delivered as two vertical slices — User Story 1
  then User Story 2 — as a stacked pull-request chain in which the second slice
  stacks on the first. [US1] [US2]
- **FR-033a**: The slice seam MUST follow this file-level allocation. Slice 1
  **creates** every file; slice 2 **extends** three of them additively and creates
  none. [US1] [US2]

  | File | Slice 1 | Slice 2 |
  | ---- | ------- | ------- |
  | `layer6-efficiency/contracts-claude/route-policy.schema.json` | create — route shape with its closed five-member effort enum, ordered fallbacks, declared budget fields **and their schema maxima**, and the optional `optional_helper` declaration (FR-025b) | unchanged |
  | `layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json` | create — all seven projection members, including declared platform route changes and the organization model allowlist (FR-002) | unchanged |
  | `layer6-efficiency/contracts-claude/route-resolution-report.schema.json` | create — `outcome` discriminator with `allOf`/`if`/`then` conditional requiredness; two diagnostic `$defs` each with its own inline `code` enum unioned by `oneOf`; the four-member sub-reason enum; the closed `remediationAction` enum (`minItems: 1`, `maxItems: 3`); per-code `severity` and the `const` `source`; the `exhausted_budget` array over its own three-member enum; attempted-route list admitting zero entries; effective dispatch tuple; `optional_helper` with its probe counter; `release_claim_eligible` | **unchanged — must stay untouched** |
  | `layer6-efficiency/lib/claude_route_fallback.py` | create — canonical serialization, snapshot projection intake, preferred-then-fallback walk, five-code semantics, `details` sub-reasons | extend — structural-validation pre-pass, budget cap enforcement with attempt counting, override handling including the allowlist-skip branch, helper-unavailable path, no-safe-route remediation |
  | `layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json` | create — `cases[]` holding the US1 resolution-failure cases with pinned reports | append the US2 cases to the end of `cases[]`, including both override cases (honored and allowlist-skipped); existing case positions and pinned bytes unchanged |
  | `unit/test-route-fallback-simulation.py` | create — resolution semantics, replay byte-identity over the simulator's own serializer, roadmap parity test, set equality on **all three** closed enums (both reason-code vocabularies and the effort ladder, FR-007a), inline negative tests for out-of-vocabulary code and out-of-range budget, corpus case-ID uniqueness and self-containment | append the US2 test functions |
  | `suite-manifest.json` | modify — append **one** entry to the layer 4 `scripts[]` array | **unchanged — must stay untouched** |
  | `docs/ai/specs/claude-agent-routing-technical-roadmap.md` | modify — status line and progress row at scaffold, plus the **Grounded Platform Facts** section (PF-1…PF-4) and the two amended scope bullets recording that the override is conditional and that CAR-002 never pinned the unavailable-model fact | untouched |
  | `docs-site/src/content/docs/reference/tests.md` | regenerate (generated; excluded from review) | regenerate |

  Registering exactly **one** test module in slice 1 is what keeps the manifest out
  of slice 2's diff: slice 1's entry becomes the tail of the `scripts[]` array, so a
  second slice-2 entry would have to add a comma to slice 1's last line. One module
  avoids that single-character churn entirely.

- **FR-033b**: The seam rule is **append-only additivity**, not "slice 2 touches no
  slice-1 file" — the latter is unachievable, because the corpus is one file by
  FR-015, the simulator is one module by FR-033d, and slice 1 cannot pre-register a
  test path that does not yet exist. Slice 2 MAY add to a slice-1 file but MUST NOT
  rewrite, reorder, rename, or re-pin anything slice 1 committed: no slice-1
  `case_id`, input, or pinned expected report may change, and no slice-1 function
  signature may change. Slice 1 MUST be complete and passing on its own, with
  nothing stubbed or `TODO`-marked for a later slice. **Schemas are out of scope for
  this rule entirely**: all three land complete in slice 1 and slice 2 modifies no
  schema file, preserving the directory's unbroken invariant that no contract document
  has ever been edited after its introducing commit. Slice 2's additive surface is
  therefore exactly three files — the simulator module, the corpus, and the unit test. If a slice-2 finding requires
  changing slice-1 content, that is evidence the slice-1 contract was wrong: the fix
  MUST land on slice 1's branch and the chain MUST be restacked — it MUST NOT be
  absorbed into slice 2's diff. [US1] [US2]
- **FR-033c**: The scenario corpus MUST remain a **single** file across both
  slices, preserving the one-self-contained-corpus decision. The seam is carried
  by the stacked branch chain — slice 2's diff is measured against slice 1's
  branch, so appended cases read as pure additions — not by splitting the corpus
  into per-slice files. [US1] [US2]
- **FR-033d**: The reference simulator MUST remain a **single** module across both
  slices, matching the repository's one-module-per-capability convention in the
  Layer 6 library. Structural policy validation is a pre-pass of the same
  route-resolution capability, not a separate capability, and MUST NOT be split
  into a second module solely to avoid a slice-2 edit. [US1] [US2]

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is claimed. The surface is entirely new test
  fixtures, schemas, a test-library simulator, and unit tests; none of it is
  generated, vendored, or `.process` content.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter (Layer 6 efficiency fixtures, schemas, and
  reference simulator) with the unit-test surface that exercises it
- **Secondary surfaces, if any**: seed/config — the test suite manifest entry for
  the new unit test
- **Projected reviewable LOC**: **0 by this repository's declared-LOC accounting**,
  and that is the honest answer rather than a favourable one. The surface has 0
  production files, and every automated signal is blind to it:
  `estimate-reviewable-loc` computes `projected = production_files × 40`
  (`speckit-pro/speckit_pro_runner/helpers/read_only.py:926`), which yields 0 and
  status `pass`; the setup gate performs no measurement at all, regex-scraping the
  number a human typed into the roadmap (`read_only.py:850`); and the PR-time packet
  gate thresholds the same author-declared figure
  (`speckit-pro/speckit_pro_runner/helpers/pr_emission.py:589-619`). Note also that
  `greenfield` evaluates **false** here because `suite-manifest.json` and the routing
  roadmap are modified rather than created (`read_only.py:923-925`), so the
  thresholds stay 400/800 rather than 600/1200.
  By **artifact lines**, which is what a reviewer actually reads: roughly
  1,900–2,700 in slice 1 and 1,200–1,900 in slice 2 — three schemas ~470–620, the
  simulator ~550–750 then +350–550, the corpus ~450–600 then +400–550, the unit test
  ~450–700 then +350–600.
  The advisory `estimate-spec-size` formula (`user_stories × 25 + files × 40 +
  frs × 15`, `read_only.py:964`) re-run on this spec's **real** signals — 2 user
  stories, 10 files, and the literal count of **60** distinct FR identifiers
  (33 base numbers plus 27 lettered sub-requirements) — returns **1,350 and 4
  suggested slices**, status `warn`. It returned 975 and 3 slices against the
  35-requirement figure carried before Clarify and the three checklist domains
  added sub-requirements, and 770/2 at scoping from coarser signals (4 stories, 10
  files, 18 FRs). The trend is monotonic upward and nothing in the estimator
  supports collapsing to one slice.
  **The two-slice election is unchanged by this**, on the grounds already recorded:
  no gate measures a 0-production-file surface, so the estimator is advisory here in
  both directions — it can no more force a third and fourth slice than it could
  overturn the split by returning a smaller number. The seam is the rule-family
  boundary, and there are two rule families. That the advisory figure now suggests
  four is recorded rather than acted on, because only an operator decision can move
  this split.
- **Projected production files**: 0
- **Projected total files**: 7 authored plus 1 generated — 3 schemas, 1 scenario
  corpus, 1 simulator library module, 1 unit test, 1 suite-manifest entry, and the
  regenerated `docs-site/src/content/docs/reference/tests.md`. Slice 2 creates no new
  authored file.
- **Budget result**: **split elected, not gate-forced.** With 0 production files every
  automated LOC signal reads 0 or `pass`, so one slice would pass every gate. The
  immediately preceding sibling spec CAR-004 — same primary surface, 0 production
  files, declared 250 reviewable LOC, status ok — shipped roughly 11,600 artifact
  lines in a single pull request (#401). The declared figure in this repository
  systematically excludes fixture JSON, platform-scoped schemas, test-library
  modules, and unit tests.
- **Split decision**: Two vertical slices, elected on **review-burden and
  independent-value grounds rather than on a LOC ceiling**. The seam is the
  rule-family boundary, each slice cutting schema through simulator through test
  end-to-end: slice 1 is User Story 1 (resolution-failure semantics — snapshot
  projection, the five resolution codes, report envelope, replay pinning); slice 2 is
  User Story 2 (structural rejections, override and helper paths, budget exhaustion,
  report-only no-safe-route). Slice 1 is independently landable and releasable and is
  the artifact CAR-006 needs first; slice 2 adds no new authored file and lands as
  append-only additive edits. The two pull requests are managed as a gh-stack chain
  with slice 2 stacked on slice 1. Because no gate measures this surface,
  plan-time or PR-time re-estimation **cannot** overturn the split by returning a
  smaller number — only an operator decision can.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Each slice's PR MUST state its position in the stacked chain and, for slice 2,
  name slice 1 as its base.

### Key Entities *(include if feature involves data)*

- **Route policy fixture**: a synthetic agent's routing intent — preferred route
  (alias, qualified resolved model ID, explicit effort), ordered qualified
  fallback routes, declared probe, retry, and fan-out budgets, and optionally a
  declared optional helper with its own routes (FR-025b).
- **Environment snapshot projection**: the minimal view of a probed environment
  that resolution consumes — available model IDs, alias-to-resolved-model
  bindings, per-model supported efforts, probe availability, exact-invocation
  probe outcomes, declared platform route changes for pinned tuples, and the
  organization model allowlist. All seven are read by a named requirement and none
  is vestigial (FR-002); this is the input contract CAR-006's preflight inherits.
- **Environment overrides**: externally imposed dispatch settings — specifically
  the `CLAUDE_CODE_SUBAGENT_MODEL` subagent-model override, which resolution must
  honor and report on rather than suppress, subject to the organization allowlist
  gate that can cause the platform to skip it (FR-024b).
- **Declared budgets**: the per-policy hard caps on probe attempts, retries, and
  fan-out, together with the actual attempt counts resolution reports back.
- **Resolution report**: the deterministic output for one scenario — attempted
  routes in order, effective dispatch tuple or unresolved status, diagnostic
  entries, release-claim eligibility, and remediation.
- **Diagnostic entry**: one rejection or remediation record in the runner
  diagnostics envelope shape, whose code is drawn from either the closed
  route-resolution enum or the closed policy-violation enum.
- **Scenario corpus case**: one self-contained replay unit bundling a policy, a
  snapshot, overrides, declared budgets, and the pinned expected report.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every scenario the roadmap mandates is represented by at least one
  corpus case — preferred model absent (including the `fable` case), **alias
  unresolved**, effort
  unsupported, probe unavailable, exact-invocation probe success, exact-invocation
  probe failure, alias re-pointing, platform route change, unqualified override,
  **override skipped by the organization allowlist**, fallback loop, unqualified
  adjacent model, generic-agent substitution, silent
  inherit materialization, helper unavailable, **retry** exhaustion, and no safe
  route — with zero mandated scenarios unrepresented. Exhaustion is named by its
  terminating class rather than as generic "budget exhaustion", because the roadmap
  states retry exhaustion as its own proof obligation (FR-028). The
  override-skipped family is this spec's own addition rather than a roadmap-named
  one, and it is mandatory for the reason FR-024b gives: without it the corpus pins
  an unconditional override effect the documented runtime does not have.
- **SC-013**: Every behaviour this feature simulates that has a documented runtime
  counterpart is traceable to that counterpart, and every place the simulation
  **deliberately diverges** from it names the divergence and its justification. The
  count of simulated behaviours asserted without either a cited runtime source or a
  recorded deliberate-divergence note is exactly zero. **Four** carry recorded
  divergences today — preflight rejection of an unsupported effort where the runtime
  silently degrades (FR-007a), sub-division of platform route change into two
  sub-reasons where CAR-002 detects one bucket (FR-006), pinning resolution
  semantics ahead of an unsettled platform fact (FR-002a), and making `severity` a
  function of `code` where the installed runner leaves it caller-determined
  (FR-012c) — and the effort ladder additionally carries a set-equality assertion
  against its frozen in-tree source (FR-007a). The count is stated because the
  criterion is only falsifiable against an enumeration: a divergence recorded
  somewhere in the requirements but missing from this list would satisfy the
  zero-count clause while defeating the traceability the criterion exists to give.
- **SC-002**: 100% of corpus cases replay byte-identically to their pinned
  expected report, and 100% replay byte-identically across two successive runs.
- **SC-003**: Both reason-code vocabularies are closed sets whose membership is
  enforced by schema validation, so an unrecognized code fails validation rather
  than passing through.
- **SC-004**: The count of production files changed is exactly zero, and the
  count of frozen CAR-002, CAR-003, and CAR-004 schemas or fixtures modified is
  exactly zero.
- **SC-005**: The count of members added to the shared byte-identical contracts
  directory is exactly zero.
- **SC-006**: The count of real shipped agent names appearing in the fixtures is
  exactly zero.
- **SC-007**: A reader who has never seen this feature can open a single corpus
  case and determine, without opening any other file, what environment it
  simulates and what report it expects.
- **SC-008**: The full repository test suite passes with zero failures, and the
  new test is dispatched through the suite manifest rather than only runnable by
  hand.
- **SC-009**: A budget-exhaustion case demonstrates that the actual attempt count
  never exceeds the declared budget for all three capped dimensions, proven at a
  declared budget of one, and the failing report enumerates every dimension spent to its
  cap so a consumer is not left to infer that from counters alone. The criterion is
  deliberately phrased as an enumeration rather than as naming the one dimension that
  terminated the walk: FR-026a establishes that no observable report content privileges
  one at-cap budget as the cause, so a success criterion promising a single culprit would
  be unmeetable by the design that satisfies the rest of this requirement.
- **SC-010**: The no-safe-route case's remediation actions are machine-readable
  and include previous-plugin-release rollback, so a consumer can act on them
  without parsing prose — and every attempted route is joinable by route key to the
  diagnostics that rejected it, so "each rejection reason" is readable per route rather
  than as an unattributed list.
- **SC-011**: Each slice is independently reviewable and passes the
  pull-request-time diff-mode reviewability gate on its own diff.
- **SC-012**: The committed resolution enum is exactly the five codes the Claude
  roadmap pins — verified by a test that fails on both a missing and an extra
  member — and the recorded cross-platform divergence on the third member is
  held as test data such that a silent change to either roadmap's spelling fails
  the suite. The count of Codex-side files changed by this feature is exactly
  zero.

## Assumptions

- The reference simulator is the executable specification and the fixture corpus
  is the durable contract; CAR-006 re-proves its production resolver against the
  same corpus rather than inheriting this simulator's code.
- The runner diagnostics envelope shape observed in the installed runner
  (`code`, `severity`, `message`, `source`, `details`, plus `remediation` with
  `summary` and `actions`) is stable enough to mirror; the report contract binds
  to that shape rather than inventing a parallel one.
- "Qualified" in fixture policies means declared-qualified by the fixture itself.
  Real route qualification is CAR-007 through CAR-010 and is not simulated here.
  This is a **different gate** from the organization model allowlist FR-024b reads:
  the allowlist is an environment configuration carried in the snapshot, while
  qualification is a per-route boolean the fixture declares. The two are independent
  in both directions (FR-024b).
- **Platform fidelity rests on a dated documentation extract, not on this spec's own
  reading.** Every claim about runtime behaviour — the subagent model-resolution
  order, the allowlist skip, the alias set and its drift, the effort ladder and its
  model-dependence — is traceable to the repository's dated, quoted extract of the
  published Claude Code documentation
  (`docs/ai/research/claude-agent-route-candidates.md`, `RES-1`–`RES-5`, `EFF-1`,
  `EFF-2`, `ALS-repoint`) and, where the program has already probed the surface, to
  the committed CAR-002 probe code. Where the documentation is silent the surface is
  recorded as a capability question rather than assumed: the unavailable-model
  dispatch outcome and the execution-time manifestation of alias re-pointing are both
  open questions in that extract, which is the ground FR-002a records. A later
  documentation change is therefore a change to a cited source, not a silent
  invalidation of an uncited assumption.
- The synthetic cast covers three role classes — a required executor, a bounded
  analyst, and an optional helper — which is sufficient to express every mandated
  scenario without adding more synthetic agents. What was **not** sufficient was the
  contract: a policy rooted on one agent identity could not express the
  required-agent-plus-optional-helper pairing the helper-unavailable scenario needs,
  so FR-025b adds the policy's helper declaration. The class count is unchanged; only
  the number of agents one policy can name changed, from one to one-plus-an-optional-helper.
- Canonical JSON serialization is no longer carried as an assumption: FR-014a pins it
  to a named in-tree function. Note that the resolved serializer emits **minimal
  separators and no indentation**, so an earlier reading of this assumption as
  implying a fixed *indentation* convention was wrong — a report serialized with
  `indent` set would not be byte-identical to one serialized without it. The corpus
  file on disk stays human-readable and indented; that is a property of the committed
  fixture's own formatting, not of the serialized report, and the two never meet
  because both sides of every byte comparison pass through the same serializer.
- The scoping-time estimate (770 reviewable LOC, 2 slices) and the roadmap's authored
  budget (257, 1 slice) are both forward guesses from coarse signals, and **neither
  measures this surface**: with 0 production files the repository's declared-LOC
  accounting reads 0. The two-slice split is elected on review burden and independent
  slice value, so plan-time re-estimation cannot overturn it by returning a smaller
  number — only an operator decision can.
- **Named follow-up for the mirroring obligation.** G56R-005 exists as a `Ready`
  roadmap entry with its own independently authored scope, and a shared parity contract
  document governs cross-platform evidence — but the obligation to mirror *this* spec's
  structural template is **not** written into G56R-005's own scope text. Per the PR
  packet requirement that deferred work name its follow-up, the follow-up is named here
  explicitly: **G56R-005** carries the mirroring of CAR-005's schemas, enums, and corpus
  organization, and any promotion of a schema to the shared byte-identical contracts
  directory is a deliberate future joint change requiring both platforms to land
  together.
- **No CAR-012-class parity debt is incurred.** `contracts-claude/` and
  `contracts-codex-specification/` are platform-scoped directories, not mirrored twins,
  and were never byte-identical: their documents carry different `$id` namespaces
  (`car-00N` versus `g56r-00N`), and their membership diverges in both directions.
  CAR-012's joint-landing rule is scoped specifically to the **separate shared**
  contracts directory whose members are verified byte-identical across platforms. FR-016
  plus SC-005 (zero members added to that shared directory) is exactly the boundary that
  keeps this feature clear of CAR-012 territory, which is what the platform-scoping
  decision was chosen to achieve.
- **Corrected premise**: the scoping input asserted that the five resolution
  codes are "mirrored line-for-line" across both routing roadmaps and that
  "parity holds". That is factually incorrect and this spec corrects it. Four
  members are byte-identical; the third diverges —
  `capability_probe_unavailable` in the Claude roadmap versus
  `capability_discovery_unavailable` in the Codex roadmap. The divergence
  appears deliberate rather than accidental: the Codex roadmap's surrounding
  scope concerns capability *discovery* and carries a Codex-only service-reroute
  distinction with no Claude analogue. The Claude roadmap therefore governs this
  platform's enum, and the divergence is pinned as test data rather than
  reconciled here — reconciling shared contract members across platforms is a
  deliberate joint two-platform landing, which is precisely the CAR-012
  situation the scoping set out not to recreate.
- The repository has no typechecker or linter gate; verification is the Python
  test suite (structural, script-safety, and unit layers).
