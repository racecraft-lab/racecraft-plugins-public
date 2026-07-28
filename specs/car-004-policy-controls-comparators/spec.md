# Feature Specification: CAR-004 Policy Controls and Adaptive Comparators

**Feature Branch**: `car-004-policy-controls-comparators`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Freeze the three AC-2.17 policy controls (unpinned,
adaptive, orchestration-changing) plus the dominance rule, margins, comparison
partition, and messaging consequence that CAR-011 will later apply, as
content-addressed, replay-validated contracts. CAR-004 itself concludes nothing
about dominance."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Freeze the policy comparators before the static core exists (Priority: P1)

[US1] The routing program is about to build one static twelve-agent routing
policy and will eventually publish an efficiency claim about it. Before any of
that work produces a result, the program freezes the three policy-level
comparators the final claim will be measured against, together with the rule
that decides whether a comparator beat the static core, the margin that makes
such a win "material", the untouched slice of workload the comparison will run
on, and the exact release wording each possible verdict permits. Everything is
recorded as content-addressed contracts and proven by replay, so a reader can
verify later that the comparators were fixed *before* anyone knew the answer.
CAR-004 draws no conclusion about which side wins — it only makes the question
un-riggable.

**Why this priority**: This is the whole feature and a single vertical slice
(reviewability estimator: 250 reviewable LOC, 1 slice, status ok). Every
downstream consumer — CAR-011's comparison, CAR-005 through CAR-010's
candidate-set boundary, the Codex twin's mirror, and release review — depends on
these contracts existing and being frozen. Freezing them after the static core
reports results would make the comparison unverifiable, which is the exact
failure mode this feature exists to prevent.

**Independent Test**: Fully testable on its own. Run the repository suite against
the delivered contracts and fixtures: the control set is closed at three, every
control replays deterministically, the reserved-partition guard fails on a
seeded violation and passes on the delivered evidence, and every dominance
verdict state resolves to exactly one permitted claim class. The three bounded
live smoke runs are then executed once by a developer on the supported
subscription authentication path to prove the execution contracts are real and
not merely declarative. No other CAR spec
needs to land first, and nothing shipped to users changes.

**Acceptance Scenarios**:

1. **Given** the frozen control registry, **When** a reader enumerates the
   controls, **Then** exactly three are present — unpinned, adaptive, and
   orchestration-changing — and an attempt to register a fourth arm (including a
   justified-high-effort arm) is rejected by an automated check. [FR-001]
2. **Given** a frozen control, **When** any hash-relevant field of its
   definition is altered — parameters, observable signals, retry or cancellation
   bounds, evidence requirements, or topology descriptor — **Then** the control's
   content address changes and the result is a new control version rather than an
   in-place edit of the existing one. [FR-002] [FR-003]
3. **Given** the frozen CAR-003 contract set, **When** the CAR-004 contracts are
   added, **Then** every CAR-004 document is a new standalone addition that
   references CAR-003 documents only by stable identifier and digest, and no
   CAR-003 member is edited, re-versioned, or removed. [FR-004] [FR-005]
4. **Given** the frozen environment contract's pinned parent-session model and
   effort, **When** the unpinned control is resolved, **Then** exactly one arm
   exists and it rides that pinned parent; **And** a different pinned parent
   yields a different control version by content address rather than a second
   concurrent arm. [FR-006] [FR-007]
5. **Given** the adaptive control's declared signal domain, **When** a reviewer
   enumerates every terminal state and every failure plane/code value the policy
   can observe, **Then** each maps to exactly one policy response, with no
   unmapped signal and no signal resolving to two responses. [FR-010]
6. **Given** the adaptive control's signal definitions, **When** they are traced
   to their sources, **Then** every one resolves to a member the frozen CAR-003
   execution-trace or score-bundle contract already publishes as stable — terminal
   state, failure plane, failure code, retry count, or a raw-token/duration budget
   threshold — and no new telemetry field is introduced. [FR-008] [FR-009]
7. **Given** an objective that has already consumed its one escalation, **When**
   a further escalation signal fires within that same objective, **Then** the
   policy does not escalate again and the objective terminates under its frozen
   retry and cancellation bounds. [FR-011] [FR-014]
8. **Given** a run of consecutive clean objectives, **When** the third
   consecutive clean pass completes, **Then** de-escalation is evaluated at the
   objective boundary and never mid-objective; **And** a non-clean objective
   before the third resets the streak so no de-escalation occurs. [FR-012]
9. **Given** the adaptive policy already sitting on the highest qualified route
   in the frozen candidate set, **When** an escalation signal fires, **Then** no
   route outside the frozen candidate set is reachable and the objective
   terminates under its frozen bounds. [FR-013]
10. **Given** a run where the platform changes the served route on its own,
    **When** the evidence row is classified, **Then** it is marked non-scorable
    and is not recorded or counted as a policy escalation. [FR-015]
11. **Given** an orchestration-changing run that spawns multiple children,
    **When** the objective-level record is produced, **Then** the aggregate is
    well-defined on every dimension the frozen Pareto rule reads; **And** the
    additive dimensions — the complete raw token vector, duration, retries, and
    compactions — equal the sum across the parent and every automatically spawned
    child, including children that failed, timed out, or were cancelled.
    [FR-016] [FR-029]
12. **Given** an orchestration-changing control definition, **When** its identity
    is computed, **Then** the topology descriptor is inside the content address,
    and the control's evidence is attributed at policy level only and never to a
    single agent's route. [FR-017] [FR-018]
13. **Given** a control that has not cleared every mandatory contract, safety,
    quality, reliability, and availability gate, **When** the comparison contract
    is applied, **Then** no dominance verdict is produced for that control
    regardless of its resource numbers. [FR-019]
14. **Given** two eligible arms, **When** the comparison is evaluated, **Then**
    material dominance is returned only if at least one component is at least 10%
    better in relative terms while no component is worse — retries and compaction
    included — and the decision uses the frozen environment-independent Pareto
    rule with no weighted scalar ranking. [FR-020] [FR-021]
15. **Given** a comparison whose components move in opposite directions, or that
    is tied, incomplete, or statistically uncertain, **When** the verdict is
    produced, **Then** it is not-dominant or inconclusive, and no messaging
    restriction is imposed. [FR-022]
16. **Given** the verdict-to-claim-class mapping, **When** any of the three
    verdict states is looked up, **Then** exactly one permitted wording class is
    returned; **And** the dominant state restricts release wording to measured
    improvement over the previous static baseline and forbids the "efficient",
    "optimal", and "best measured" claim classes. [FR-024]
17. **Given** the reserved CAR-011 comparison partition declared with
    content-addressed membership, **When** a replay row or smoke row is seeded to
    reference a reserved member, **Then** the guard fails; **And** on the
    delivered evidence set the guard passes. [FR-025] [FR-026]
18. **Given** the delivered evidence set, **When** it is audited, **Then** it
    contains zero outcome-bearing scored rows, consumes zero selection or
    confirmation partition objectives, and every smoke row is explicitly labeled
    non-scored. [FR-027] [FR-030]
19. **Given** the replay fixtures for all three controls, **When** they are
    replayed twice, **Then** both runs produce byte-identical results. [FR-028]
20. **Given** a developer on the supported subscription authentication path,
    **When** the three bounded live smoke runs are executed, **Then** each
    completes inside all four declared bounds (at most 5 non-reserved objectives,
    1 repetition, a 1,000,000 raw-token ceiling, a 30-minute wall clock) recorded
    through the frozen budget fields; **And** the recorded `authentication_mode`
    matches the mode actually observed and no run required an API key; **And**
    they demonstrate respectively a real dispatch-time escalation, a real inherit
    resolution, and a real parallel dispatch with child aggregation.
    [FR-030] [FR-031]
21. **Given** consecutive smoke runs for different controls, **When** their cache
    state is inspected, **Then** no control's smoke has warmed another arm's
    cache; **And** per-run smoke outputs are absent from version control while
    consolidated and contract artifacts are present. [FR-032] [FR-033]
22. **Given** the twin-handoff record, **When** the Codex twin's owner reads it,
    **Then** it enumerates every new contract member, enum, and identifier to
    mirror, records the three-control composition as a sanctioned platform
    divergence rather than parity drift, and routes any member the twin cannot
    mirror onto the reconciliation list. [FR-034] [FR-035] [FR-036]
23. **Given** the frozen comparison contract, **When** it is inspected, **Then**
    it declares exactly one confidence method and exactly one multiplicity
    position covering CAR-011's predeclared secondary control arms. [FR-023]

### Edge Cases

- **Escalation already spent**: an escalation signal fires a second time inside
  one objective. The policy must not escalate again; the objective terminates
  under its frozen bounds. [FR-011]
- **Ceiling reached**: the adaptive policy is already on the highest qualified
  route when an escalation signal fires. No route outside the frozen candidate
  set may be selected. [FR-013]
- **Streak interrupted**: a non-clean objective lands before the third
  consecutive clean pass. The counter resets and no de-escalation occurs, so the
  policy cannot oscillate between adjacent routes. [FR-012]
- **Platform-initiated reroute**: the served route changes without the policy
  asking. The row is non-scorable and must never be read as policy escalation —
  otherwise the adaptive control's measured behavior would include work it did
  not choose. [FR-015]
- **Child failure inside an orchestration run**: a spawned child fails, times
  out, or is cancelled. Its consumed resources still aggregate into the parent's
  objective-level record; discarding them would make the control artificially
  cheap. [FR-016]
- **Zero-child orchestration run**: an orchestration-changing run spawns no
  children. The aggregate equals the parent's own consumption and the row is
  still valid, not an error. [FR-016]
- **Parent session re-pinned**: the environment contract's pinned parent-session
  model or effort changes. This produces a new unpinned control version by
  content address; it must never be applied as an in-place edit to the frozen
  arm. [FR-007]
- **Mixed component movement**: one component clears the margin while another
  worsens. The result is no dominance and no messaging restriction — never a
  partial or "directional" dominance claim. [FR-022]
- **Zero-valued baseline component**: a component's comparator value is zero, so
  a relative margin is arithmetically undefined. The frozen registry must define
  the outcome rather than leaving it to the evaluator at comparison time. See the
  open margin-semantics question on [FR-021].
- **Smoke bound reached mid-run**: a live smoke hits its token ceiling or wall
  clock before finishing its objectives. The run stops at the bound and remains
  valid non-scored evidence; it must not silently exceed the declared budget.
  [FR-030]
- **Accidental reserved-partition reference**: a fixture or smoke row references
  a reserved objective. The guard must fail loudly before the evidence is
  consumed, not after. [FR-026]
- **Unmirrorable member**: the Codex twin cannot mirror a new member. It joins
  the reconciliation list rather than being silently dropped or quietly reshaped
  on this side. [FR-036]

## Requirements *(mandatory)*

### Functional Requirements

#### Control set and identity

- **FR-001**: The frozen control set MUST contain exactly three policy controls —
  unpinned, adaptive, and orchestration-changing — and MUST be closed. No fourth
  arm may be registered; in particular no justified-high-effort arm, because the
  all-max immutable production comparator already occupies that role on this
  platform.
- **FR-002**: Each control MUST carry a content address computed over its
  complete frozen definition — execution contract, parameters, observable
  signals, retry and cancellation bounds, evidence requirements, the adaptive
  control's ordered route sequence, and (for the orchestration-changing control)
  the topology descriptor — so that changing any hash-relevant field yields a new
  control identity instead of mutating an existing one. Each control and the
  comparison contract MUST additionally record a freeze timestamp alongside the
  content address, following the `frozen_at` precedent already frozen in the
  experiment-assignment contract.
- **FR-003**: Each control MUST declare its execution contract: the parameters it
  sets at dispatch time, the observable signals it reads, its retry and
  cancellation bounds, and the evidence rows a run must produce to be valid.
- **FR-004**: Control and comparison contracts MUST be authored as new,
  standalone, additive contract documents placed alongside the frozen CAR-003
  contract set (`tests/speckit-pro/layer6-efficiency/contracts-claude/`), and
  MUST reference CAR-003 contracts only by their stable identifier (`$id`) and
  digest.
- **FR-005**: No frozen CAR-003 contract member MUST be edited, re-versioned, or
  removed by this feature, including every member already listed for CAR-012
  reconciliation. Mirrored members change only by joint change with the twin.

#### Unpinned control

- **FR-006**: The unpinned control MUST freeze exactly one arm, bound to the
  parent-session model and effort already pinned by the frozen environment
  contract; its agents omit the model or set it to inherit and ride the session
  model.
- **FR-007**: A different pinned parent session MUST produce a different unpinned
  control version by content address. No matrix over multiple parent sessions may
  be frozen.

#### Adaptive control

- **FR-008**: The adaptive control's escalation and de-escalation signals MUST
  bind exclusively to members the frozen CAR-003 execution-trace and score-bundle
  contracts already publish as stable: terminal state, failure plane, failure
  code, retry count, and raw-token/duration budget thresholds.
- **FR-009**: This feature MUST NOT introduce any new telemetry field and MUST
  NOT reopen the frozen CAR-002 telemetry profile.
- **FR-010**: The adaptive signal-to-response mapping MUST be total over its
  declared signal domain: every observable terminal state and every failure
  plane/code value maps to exactly one policy response, with no unmapped signal
  and no signal resolving to more than one response.
- **FR-011**: The adaptive policy MUST permit at most one escalation per
  objective, and that escalation MUST target the next-higher qualified route
  only. "Next-higher" MUST be defined by an explicit ordered route sequence over
  the frozen candidate set, declared as a hash-relevant member of the control's
  frozen definition rather than inferred when fixtures are authored.
  [NEEDS CLARIFICATION: the total order over the frozen (model, effort) candidate
  set that defines "next-higher qualified route". The effort ladder is closed and
  ordered, but model is an unordered string in the frozen successor-capability
  contract, so a candidate set spanning two models has no total order yet, and an
  escalation fixture would otherwise encode an ordering this spec never froze.
  Routed to the numeric-registry Clarify session.]
- **FR-012**: The adaptive policy MUST decide de-escalation only between
  objectives, only after N = 3 consecutive clean passes, and never mid-objective.
- **FR-013**: Every route the adaptive policy can escalate or de-escalate to MUST
  lie inside the frozen candidate set, and a route outside that set MUST be
  unreachable by construction rather than merely discouraged.
- **FR-014**: The adaptive control MUST declare explicit retry and cancellation
  bounds that a deterministic replay can prove were respected.
- **FR-015**: A platform-initiated route change MUST be classified as
  non-scorable and MUST NOT be recorded or counted as a policy escalation.

#### Orchestration-changing control

- **FR-016**: The orchestration-changing control MUST account resources as a
  parent-plus-children aggregate whose combining rule is defined for every
  dimension the frozen Pareto rule consumes, not only the additive ones. The
  additive dimensions — the complete raw token vector, duration, retries, and
  compactions — sum across the parent and every automatically spawned child,
  including children that failed, timed out, or were cancelled.
  [NEEDS CLARIFICATION: the parent-level aggregation rule for the two
  non-continuous frozen Pareto dimensions, acceptance and terminal state, when a
  spawned child fails, times out, or is cancelled. Neither is a sum — terminal
  state is a closed enum and acceptance is number-or-null — so the multi-child
  replay fixture has no expected value for them. Routed to the numeric-registry
  Clarify session, to be answered together with the related FR-021 question about
  how those same two dimensions participate in the dominance test.]
- **FR-017**: The orchestration-changing control MUST carry a content-addressed
  topology descriptor as part of its frozen identity.
- **FR-018**: The orchestration-changing control MUST be evaluated at policy
  level only and MUST NOT be attributed as evidence about any single agent's
  route.

#### Comparison contract

- **FR-019**: The comparison contract MUST freeze the control-eligibility floors:
  a control becomes eligible for a dominance verdict only after it passes every
  mandatory contract, safety, quality, reliability, and availability gate — the
  same mandatory gates candidates face.
- **FR-020**: Dominance MUST be decided by the environment-independent Pareto
  rule already frozen for CAR-003, applied over the complete raw resource vector.
  No weighted scalar ranking may be introduced or forced.
- **FR-021**: Material dominance MUST require at least one component at least 10%
  better in relative terms while no component is worse, with retries and
  compaction included in the "no component worse" test.
  [NEEDS CLARIFICATION: margin semantics — which of the frozen Pareto dimensions
  are margin-eligible versus no-worse-only; how the two non-continuous dimensions
  (acceptance and terminal state) participate in the material-dominance test; and
  what a zero-valued comparator component yields when a relative margin is
  arithmetically undefined. Routed to the numeric-registry Clarify session.]
- **FR-022**: A mixed, tied, inconclusive, or incomplete comparison MUST yield no
  dominance verdict and MUST impose no messaging restriction.
- **FR-023**: The comparison contract MUST freeze the confidence method and the
  multiplicity position of CAR-011's predeclared secondary control arms. The
  concrete alpha allocation is routed with the other pending numerics recorded in
  Assumptions below.
- **FR-024**: The comparison contract MUST carry a machine-readable
  verdict-to-claim-class mapping that is total over the verdict states dominant,
  not-dominant, and inconclusive. The dominant state MUST restrict release wording
  to measured improvement over the previous static baseline and MUST forbid the
  "efficient", "optimal", and "best measured" claim classes.

#### Reserved comparison partition

- **FR-025**: A named comparison partition reserved for CAR-011 MUST be declared
  in the existing corpus/partition registry with content-addressed membership.
- **FR-026**: An automated guard MUST fail if any CAR-004 replay row or smoke row
  references a member of the reserved partition, and MUST pass on the delivered
  evidence set.
- **FR-027**: This feature MUST produce no outcome-bearing scored evidence and
  MUST consume no selection or confirmation partition objectives.

#### Validation

- **FR-028**: Every control MUST be validated by deterministic synthetic replay
  fixtures that reproduce byte-identically across repeated runs.
- **FR-029**: Replay coverage MUST include a multi-child orchestration case
  proving the aggregate is well-defined on every dimension the frozen Pareto rule
  reads, and that the additive dimensions equal the sum across the parent and
  every child.
- **FR-030**: Each control MUST have exactly one bounded live smoke run. The
  smoke MUST NOT require API-key authentication and MUST be executable on the
  product's supported subscription authentication path, per the PRD AC-2.19
  amendment of 2026-07-26 forbidding any supported path that requires an API key.
  The observed authentication mode MUST be recorded through the already-frozen
  `authentication_mode` field rather than a newly coined one. Each run is bounded
  to at most 5 non-reserved objectives, 1 repetition, a 1,000,000 raw-token
  ceiling, and a 30-minute wall clock, recorded through the frozen budget fields,
  with every smoke row explicitly labeled non-scored.
- **FR-031**: The three smoke runs MUST demonstrate, respectively, a real
  dispatch-time escalation (adaptive), a real inherit resolution (unpinned), and a
  real parallel dispatch with child aggregation (orchestration-changing).
- **FR-032**: Smoke runs MUST preserve cache isolation between arms so that no
  control's smoke warms another arm's cache.
- **FR-033**: Per-run smoke outputs MUST stay out of version control; only
  consolidated and contract artifacts are committed.

#### Twin handoff

- **FR-034**: A CAR-004 twin-handoff record MUST enumerate every new contract
  member, enum, and identifier the Codex twin (G56R-004) must mirror.
  [NEEDS CLARIFICATION: the exact mirror-membership set and the coordination
  timing with the G56R-004 owner — the twin is ready but unstarted. Routed to the
  twin-parity Clarify session.]
- **FR-035**: The twin-handoff record MUST record the three-control composition
  as a sanctioned platform divergence from the twin's differently named third
  control, so it does not read as parity drift.
- **FR-036**: Any member the twin cannot mirror MUST be routed onto the
  CAR-012-class reconciliation list rather than silently dropped or reshaped on
  this side.

### Reviewability Notes

- Setup-gate result (2026-07-27): pass. Reviewable LOC 250, production files 0,
  total files approximately 10, primary surface harness/fixtures, 1 slice. No
  split decision required and no typed reviewability exception is claimed.
- The surface is repository-only validation: no plugin runtime, payload, or
  shipped-default behavior changes.

### Key Entities

- **Policy Control**: One frozen, content-addressed evaluation fixture
  representing a policy-level alternative to the static core. Exactly three
  exist: unpinned, adaptive, orchestration-changing.
- **Control Identity (content address)**: The digest computed over a control's
  complete frozen definition. Any hash-relevant change produces a new identity, so
  a control can be superseded but never quietly mutated.
- **Execution Contract**: A control's declared dispatch-time parameters,
  observable signals, retry and cancellation bounds, and required evidence rows.
- **Adaptive Policy**: The frozen escalation/de-escalation rule set — its signal
  domain, its total signal-to-response mapping, its one-escalation-per-objective
  ceiling, and its N = 3 between-objective de-escalation threshold.
- **Topology Descriptor**: The content-addressed shape of an
  orchestration-changing run (fan-out and child structure), part of that control's
  identity and the basis for its aggregate accounting.
- **Control Comparison Contract**: The frozen rules CAR-011 will apply —
  eligibility floors, the Pareto dominance rule, the per-component relative
  margin, the confidence method and multiplicity position, the reserved-partition
  binding, and the messaging mapping.
- **Dominance Verdict**: One of dominant, not-dominant, or inconclusive, produced
  only for an eligible control.
- **Claim Class**: A permitted class of release wording. The mapping from verdict
  to claim class is machine-readable and total.
- **Reserved Comparison Partition**: The named, content-addressed set of workload
  objectives held untouched for CAR-011's comparison.
- **Replay Fixture**: A deterministic synthetic record set that reproduces a
  control's behavior byte-identically without live execution.
- **Bounded Smoke Record**: A single non-scored live run per control, executed
  inside the four declared bounds, proving the execution contract is real.
- **Twin-Handoff Record**: The enumerated list of new members the Codex twin must
  mirror, plus the sanctioned divergence note and the reconciliation routing rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The frozen control set enumerates exactly three controls, and an
  attempt to register a fourth is rejected automatically rather than by reviewer
  vigilance. [FR-001]
- **SC-002**: For all three controls, altering any hash-relevant field changes the
  control's content address — demonstrated once per control. [FR-002]
- **SC-003**: 100% of the adaptive policy's declared signal domain maps to exactly
  one policy response, with zero unmapped signals and zero ambiguous mappings.
  [FR-010]
- **SC-004**: Zero frozen CAR-003 contract members are modified, verifiable from
  the change set alone without running anything. [FR-005]
- **SC-005**: All three controls replay deterministically, producing byte-identical
  results across repeated runs. [FR-028]
- **SC-006**: The multi-child orchestration replay proves the aggregate is
  well-defined on every dimension the frozen Pareto rule reads, and that the
  additive dimensions equal the sum across the parent and every child. [FR-029]
- **SC-007**: The reserved-partition guard fails on a seeded violation and passes
  on the delivered evidence set — non-consumption is machine-checked, not asserted
  in prose. [FR-026]
- **SC-008**: Every dominance verdict state resolves to exactly one permitted
  claim class, so a release reviewer can determine permitted wording without
  exercising judgment. [FR-024]
- **SC-009**: Each control's live smoke completes inside all four declared bounds
  (at most 5 objectives, 1 repetition, 1,000,000 raw tokens, 30 minutes) and every
  smoke row is labeled non-scored. [FR-030]
- **SC-010**: The evidence CAR-004 emits contains zero outcome-bearing scored rows
  and consumes zero selection or confirmation partition objectives. [FR-027]
- **SC-011**: The twin-handoff record enumerates 100% of the new contract members,
  so the twin owner can mirror the surface without re-deriving it from the diff.
  [FR-034]
- **SC-012**: Every control and the comparison contract carry a recorded freeze
  timestamp and a content address in a committed artifact, and an automated check
  recomputes each digest and confirms it matches the recorded one. [FR-002]

## Out of Scope

- **Concluding dominance.** CAR-004 freezes the question and the rule; CAR-011
  owns the comparison and the answer. No CAR-004 artifact states or implies which
  side wins.
- **Any production adaptive-routing or orchestration feature.** The adaptive and
  orchestration-changing controls are evaluation fixtures only. No shipped routing
  behavior, scheduler, or agent default changes.
- **Edits to frozen CAR-003 schemas**, including every mirrored member already on
  the CAR-012 reconciliation list. Additive-only, without exception.
- **New telemetry fields**, and any reopening of the frozen CAR-002 telemetry
  profile. Every adaptive signal binds an already-stable member.
- **An unpinned-control matrix over multiple parent sessions.** One arm, one
  pinned parent; a different parent is a different control version.
- **Scored smoke rows.** Every smoke row is non-scored, so the scored-campaign
  evidence rules do not attach to it. Authentication mode is not the reason —
  the smoke runs on the same supported subscription path as scored work.
- **Scored mini-campaigns per control.** CAR-004 is barred from producing
  outcome-bearing evidence.

## Assumptions

- **Source of truth for scoping.** `docs/ai/specs/.process/CAR-004-design-concept.md`
  records all fifteen scoping decisions with rationale. Where this spec compresses
  a decision, that document governs.
- **CAR-003 is landed and frozen.** The evaluation runner, contract set, role
  corpus, partition registry, and analysis machinery already exist and are stable
  enough to reference by identifier and digest.
- **The environment contract already pins a parent session.** The unpinned control
  binds to that existing pin rather than establishing one.
- **"Clean pass" means an accepted objective** with no candidate-caused failure,
  no retry, and no budget breach. It is defined against already-frozen terminal
  state and failure classification rather than a new notion of success.
- **Repository-only surface.** Delivery is validation assets under the existing
  test tree: additive contract documents, validators, replay fixtures, registry
  entries, a guard test, and a bounded smoke harness entry. The twin-handoff
  record lands in `docs/ai/specs/.process/`, matching the CAR-003 precedent — it
  is cross-platform coordination, not repository validation.
  Tooling stays on the Python 3.11+ standard library, and script and test
  filenames stay durable — never coupled to the spec ID.
- **Live smoke is developer-local.** It is run by hand on the supported
  subscription authentication path, not in CI, and its per-run outputs stay
  untracked.
- **Numeric values are interview-frozen but registry-pending.** The 10% relative
  margin, N = 3, and the smoke caps are settled as decisions; their final
  serialization into the content-addressed registry materializes during Plan and
  Implement. The 1,000,000-token and 30-minute ceilings were recorded at
  moderate confidence.
  [NEEDS CLARIFICATION: final registry serialization of the frozen numerics — the
  per-component margin map, the N = 3 threshold, the smoke caps, and the
  alpha/multiplicity allocation for CAR-011's predeclared secondary control arms.
  Routed to the numeric-registry Clarify session.]
- **Downstream consumers.** CAR-011 applies these contracts; CAR-005 through
  CAR-010 inherit the frozen candidate-set boundary and the reserved-partition
  guard; G56R-004 mirrors the new members; release reviewers read the messaging
  mapping.
