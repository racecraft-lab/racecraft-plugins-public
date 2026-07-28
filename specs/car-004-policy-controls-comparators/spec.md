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
24. **Given** the twin-handoff record and the committed contract documents and
    registry entries, **When** the automated check re-derives the mechanically
    derivable categories, **Then** it fails on any difference in either
    direction — a delivered member absent from the record, or a recorded member
    absent from the artifacts — and it also rejects any entry carrying no mirror
    obligation or more than one. [FR-034] [FR-034a]
25. **Given** the record's sanctioned-divergence section, **When** it is
    audited, **Then** it holds exactly one entry, the three-control
    composition, stated well enough to reach the sanctioned-divergence
    conclusion without opening either roadmap; **And** a second divergence, or
    one classified against a contract document, declared member, frozen
    numeric, or decision-semantics entry, fails the check. [FR-035] [FR-035a]
26. **Given** the record at publication, **When** its mirror obligations are
    enumerated, **Then** the reconciliation candidate list is explicitly stated
    as empty and every entry is `mirror_required` or the single sanctioned
    divergence. [FR-036a]
27. **Given** the CAR-004 implementation pull request, **When** its merge
    preconditions are checked, **Then** the only coordination obligations are
    that the record is committed in that pull request and that it states its
    publication date and the reference by which the G56R-004 owner was
    notified; **And** no twin acknowledgment, response, or landing gates the
    merge; **And** the record is not a hash-relevant input to any control's or
    the comparison contract's content address. [FR-037] [FR-037a]
28. **Given** the adaptive control's declared `escalation_ladder`, **When** the
    automated well-formedness check runs, **Then** the ladder binds exactly one
    successor-capability freeze by identifier and digest, carries every admitted
    tuple exactly once with no duplicate and no omission, agrees with the frozen
    closed effort ladder wherever two entries share a `model`, and carries a
    recorded rationale at every cross-model step; **And** reordering the ladder
    yields a new adaptive-control content address rather than an in-place edit of
    the existing one. [FR-011a] [FR-011b]
29. **Given** an orchestration-changing run whose parent completed but one
    spawned child failed, timed out, or was cancelled, **When** the
    objective-level record is produced, **Then** the aggregate terminal state is
    the most severe member present under the frozen `terminal_state_severity`
    order and is therefore not `completed`; **And** the aggregate acceptance is 0
    rather than summed, averaged, or omitted; **And** the failed child's consumed
    resources still sum into the additive dimensions rather than being dropped.
    [FR-016a] [FR-016b] [FR-016c]
30. **Given** two eligible arms whose comparison the frozen Pareto rule resolves
    in the candidate's favour, **When** the materiality filter is applied,
    **Then** only `input_tokens`, `cached_input_tokens`, `output_tokens`, and
    `duration` can clear the 0.10 margin while `retries`, `compactions`,
    `acceptance`, and `terminal_state` can only defeat dominance by being worse;
    **And** a component whose comparator value is zero is recorded
    `margin_not_computable` rather than read as an infinite or 100% improvement;
    **And** a differing terminal state or a null acceptance yields inconclusive.
    [FR-021] [FR-021a] [FR-021b] [FR-021c] [FR-021d] [FR-021e]
31. **Given** the two new committed contract documents, **When** their frozen
    instances are validated, **Then** the registry's `smoke_bounds` raw-token
    members sum to exactly 1,000,000 as a machine-checked identity; **And**
    neither document resolves a reference outside its own `#/$defs/`; **And** the
    `secondary_control_arm_family` is declared in the comparison contract,
    disjoint from the frozen analysis plan's three families rather than added to
    them. [FR-004] [FR-023] [FR-030]

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
  a relative margin is arithmetically undefined. The frozen registry defines the
  outcome rather than leaving it to the evaluator at comparison time: the
  component is recorded `margin_not_computable`, contributes nothing to the "at
  least one cleared" disjunction, and is never read as an infinite or 100%
  improvement. [FR-021c]
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
  That sequence MUST be declared as `escalation_ladder`, an ordered array of
  `candidate_route_id` strings carried as a hash-relevant member of the adaptive
  control's frozen definition under FR-002. Rank is array position and nothing
  else: the next-higher qualified route for the route at index i is the entry at
  index i + 1, the highest qualified route is the final entry, and the
  de-escalation of FR-012 targets index i - 1. Order MUST NOT be inferred from the
  `admitted_tuples` array order of the bound successor-capability freeze, from a
  model name, from an alphabetical sort, or from any other derived source; that
  array is emitted model-lexicographic and then ladder-ordered for serialization
  determinism only, so reading it as a capability order would silently encode
  alphabetical rank as capability rank.
- **FR-011a**: `escalation_ladder` MUST satisfy four well-formedness rules that an
  automated check enforces fail-closed:
  1. **Binding and membership** — the control binds exactly one
     successor-capability freeze by `candidate_freeze_id` and `freeze_digest`, and
     every ladder entry resolves to the `candidate_route_id` of one of that
     freeze's `admitted_tuples`.
  2. **Totality** — the ladder carries every admitted tuple exactly once, with no
     duplicates and no omissions. A route that must not be reachable MUST be
     removed at the freeze through `excluded_tuples` and its closed `reason` enum,
     never by omission from the ladder, so FR-013's "unreachable by construction"
     holds without a second, unreviewed exclusion mechanism.
  3. **Within-model order is derived** — for any two entries sharing a `model`,
     their relative ladder positions MUST agree with the frozen closed effort
     ladder low, medium, high, xhigh, max. Where the repository already fixes an
     order, the declaration MUST agree with it.
  4. **Cross-model order is authored** — `model` is an unordered string in the
     frozen contract, so an entry whose `model` differs from its predecessor's is
     a declared capability judgment: it MUST carry a non-empty rationale recorded
     as an FR-034 category 7 decision-semantics entry. No rule may derive
     cross-model rank from a model identifier, alias, release date, or catalog
     position. When the admitted set spans a single model the ladder is fully
     derived and nothing is authored.
- **FR-011b**: The ladder MUST be content-addressed by SHA-256 over the canonical
  JSON of the control record in declared array order, never sorted, so reordering
  it yields a new adaptive-control version instead of mutating one, and a re-freeze
  that drops or excludes any entry invalidates the control rather than silently
  re-ranking it. The final entry has no successor and the first has no predecessor:
  an escalation signal fired at the ceiling records no escalation, wrap-around is
  refused, and the objective terminates under the FR-014 retry and cancellation
  bounds.
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
  The two non-continuous dimensions combine as follows.
- **FR-016a**: Aggregate terminal state MUST be the worst-wins fold over the
  parent and every automatically spawned child, taken against
  `terminal_state_severity` — an explicit six-member ordered array restated in
  full as a hash-relevant member of the orchestration-changing control's frozen
  definition: completed, failed, timed_out, cancelled, budget_exhausted,
  abandoned, severity increasing left to right. The aggregate is the most severe
  member present across the unit, so it is `completed` only when the parent and
  every child are `completed`; one failed, timed-out, or cancelled child makes it
  non-completed; and a run with no children folds to the parent's own state and is
  a valid row rather than an error. Worst-wins rather than parent projection is
  required because a projection would let an orchestration run spray failing
  children and still report a clean state with the cost charged, which is the
  artificial-cheapness failure this aggregate exists to prevent. The array MUST be
  validated set-equal, not order-equal, to the frozen score-bundle terminal-state
  enum, so no member can be left unmapped while a later reordering of the mirrored
  enum cannot silently change a CAR-004 verdict. This severity rank is
  aggregation-only: FR-021 keeps terminal state categorical and unordered for
  comparison, and both halves MUST appear as separate FR-034 category 7
  decision-semantics entries so a mirroring implementation cannot collapse them.
- **FR-016b**: Aggregate acceptance MUST be the objective-level acceptance-oracle
  result for the parent objective, and it MUST NOT be summed, averaged, minimized,
  maximized, or otherwise combined across children; children are not objectives
  and carry no acceptance of their own, and a per-child statistic would be the
  weighted scalar composite the frozen policy prohibits. Whenever the aggregate
  terminal state is any member other than `completed`, acceptance MUST be 0,
  matching the frozen candidate-failure acceptance constant. A failed, timed-out,
  or cancelled child therefore floors the unit's acceptance while its consumed
  resources still sum into the additive dimensions; no child is ever dropped from
  the unit or filtered out of the estimand.
- **FR-016c**: Acceptance MAY be null only when the acceptance oracle did not run
  at all. Null is an evidence gap, never an imputed zero: it makes the dominance
  comparison uncertain and yields no verdict under FR-022, and it MUST be reported
  rather than filtered. A child's missing value never induces a null aggregate,
  and every committed replay fixture row MUST carry a non-null aggregate
  acceptance.
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
  Margin-eligible dimensions are exactly the four ratio-scale cost quantities —
  `input_tokens`, `cached_input_tokens`, `output_tokens`, and `duration` — each
  carrying a relative margin of 0.10. The remaining four — `retries`,
  `compactions`, `acceptance`, and `terminal_state` — are no-worse-only: none of
  them can ever supply material dominance, and any of them being worse defeats it.
  Retries and compactions are excluded from the margin because they are
  small-integer counts at which a 10% relative change is not representable, and
  because the frozen analysis plan already governs them with absolute p95 ceilings
  rather than relative comparisons. The per-component margin map MUST be total
  over all eight dimensions — each entry either margin-eligible with its relative
  margin, unit, and direction, or no-worse-only with its reason — with no
  dimension omitted.
- **FR-021a**: Material dominance MUST be decided in a fixed order that does not
  replace FR-020: first the FR-019 eligibility floors, then the frozen Pareto rule
  over the eight dimensions, and only when that rule returns candidate dominance,
  the margin test as a second-stage materiality filter. The resulting verdict map
  is total over the frozen comparison outcomes: candidate dominance with at least
  one margin-eligible component clearing its margin yields dominant; candidate
  dominance with no component clearing it yields not-dominant, because the
  evidence was sufficient and the materiality bar simply was not cleared;
  comparator dominance yields not-dominant; and a tie, a mixed result, or an
  uncertain result yields inconclusive under FR-022.
- **FR-021b**: Acceptance and terminal state MUST participate through the "no
  component worse" half only. Acceptance is higher-is-better, so no-worse means
  the candidate value is at least the comparator value; a strictly higher
  acceptance is recorded and reported but never satisfies the margin trigger, so a
  control that is cheaper because it gave up can never read as materially
  dominant. Terminal state is categorical and unordered, so no-worse means equal
  and any difference makes the comparison mixed and therefore inconclusive with no
  messaging restriction; a percentage on it is undefined by construction, and the
  FR-016a severity rank MUST NOT be read here. A null or absent value on either
  dimension makes that dimension uncertain and the whole comparison inconclusive.
- **FR-021c**: The margin denominator MUST be the comparator's value, matching
  FR-024's measured improvement over the previous static baseline, and a component
  whose comparator value is zero MUST be recorded `margin_not_computable`: it
  contributes nothing to the "at least one cleared" disjunction and MUST NOT be
  read as an infinite, undefined, or 100% improvement. On the four margin-eligible
  dimensions this is a fail-closed guard rather than a live branch, since all four
  are integers with a frozen minimum of 0 and a component can only be strictly
  better when the comparator value exceeds the candidate value, which makes the
  denominator positive. When every margin-eligible component records
  `margin_not_computable`, the verdict is not-dominant rather than inconclusive.
- **FR-021d**: A margin clears when the one-sided lower confidence bound on that
  component's relative improvement, computed by the single confidence method
  frozen under FR-023, is at least 0.10; a bare point estimate would let noise
  trigger a messaging restriction and would leave FR-022's statistically uncertain
  branch with no mechanism. Where a deterministic replay fixture exercises the
  rule on a single synthetic row, the point estimate stands in for the bound and
  the row remains non-outcome-bearing under FR-027.
- **FR-021e**: The comparison contract MUST freeze the dimension-name projection
  from the frozen score bundle's resource vector onto the frozen decision-vector
  names, in particular `duration_ms` to `duration`. The frozen Pareto rule refuses
  any key outside its eight dimensions, so an unprojected resource vector raises
  rather than comparing, and the projection MUST NOT be left implicit.
- **FR-022**: A mixed, tied, inconclusive, or incomplete comparison MUST yield no
  dominance verdict and MUST impose no messaging restriction.
- **FR-023**: The comparison contract MUST freeze the confidence method and the
  multiplicity position of CAR-011's predeclared secondary control arms. The
  concrete alpha allocation is the 0.05 recorded in Assumptions below, adopted
  from the frozen CAR-003 instance rather than invented here.
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

- **FR-034**: CAR-004 MUST deliver a twin-handoff record at
  `docs/ai/specs/.process/CAR-004-twin-handoff.md`, following the CAR-003
  precedent, and that record MUST enumerate the complete mirror-membership set
  in exactly these eight categories, with none left implicit:
  1. **Contract documents** — every new schema document added under
     `tests/speckit-pro/layer6-efficiency/contracts-claude/`, identified by
     `$id`, declared `schema_version`, and the SHA-256 of its committed bytes.
  2. **Declared members** — for every new `$def` and object, the declared
     property set and the `required` subset, each addressed by JSON Pointer.
  3. **Closed enumerations** — every new `enum` and `const` together with every
     one of its members: the three control identifiers, the adaptive policy
     responses, the dominance verdict states (dominant, not-dominant,
     inconclusive), and the claim classes.
  4. **Stable identifiers** — the three control IDs, the reserved comparison
     partition name, the topology descriptor ID, the registry entry keys, and
     the `$id` URIs themselves.
  5. **Bindings into frozen CAR-003 contracts** — every CAR-003 `$id` and
     digest this feature references under FR-004, so the twin binds its own
     G56R-003 counterpart rather than re-deriving the reference.
  6. **Frozen numerics** — every value the content-addressed registry freezes,
     with its unit and comparison direction: the per-component relative margin
     map, N = 3, the four smoke bounds (5 non-reserved objectives, 1
     repetition, 1,000,000 raw tokens, 30 minutes), and the confidence method
     with its alpha and multiplicity allocation.
  7. **Decision semantics that add no schema member** — the rules two
     conforming implementations must both adopt to reach the same verdict on
     identical evidence: the total adaptive signal-to-response mapping, the
     ordered route sequence that defines "next-higher qualified route", the
     parent-plus-children aggregation rule for every dimension the frozen
     Pareto rule reads, the eligibility floors, the material-dominance margin
     test, and the verdict-to-claim-class mapping. This category is mandatory
     because CAR-003's direction-of-preference rule was semantics rather than
     schema shape, was therefore absent from the schema-shaped handoff surface,
     and became an open twin gap.
  8. **Enforcement guards** — the reserved-partition non-consumption guard and
     the closed-at-three control-registry check, stated as required behavior
     rather than as Claude-side code to copy.

  Every entry MUST carry its category, its member identifier, the owning
  contract `$id`, whether it is hash-relevant under FR-002, the CAR-004
  requirement it implements, a one-line rationale, and exactly one mirror
  obligation drawn from the closed set `mirror_required`,
  `sanctioned_divergence`, and `car_owned` — the last meaning the member has no
  counterpart on the twin side and the twin owes nothing, following the
  CAR-owned precedent already frozen in the score-bundle contract. An entry
  carrying no obligation, or more than one, MUST be rejected.
- **FR-034a**: The mechanically derivable portion of the record — categories 1
  through 6 — MUST be derived from the committed contract documents and
  registry entries rather than hand-transcribed, and an automated check MUST
  re-derive that member set and fail on any difference in either direction
  between the record and the delivered artifacts, so the SC-011 completeness
  claim is machine-verified rather than attested. The check MUST stay on the
  Python 3.11+ standard library and its filename MUST stay durable rather than
  coupled to the spec ID; the record itself follows the existing
  `.process/<SPEC-ID>-twin-handoff.md` document convention.
- **FR-035**: The record MUST carry a "Sanctioned platform divergences"
  section, kept separate from the mirror-membership set, whose single entry is
  the three-control composition. That entry MUST state: the authority on each
  side — this platform freezes unpinned, adaptive, and orchestration-changing
  under PRD AC-2.17, while the Codex roadmap names unpinned, adaptive, and
  justified high-effort and treats orchestration-changing as a modifier of a
  control rather than a separate arm; the reason the difference is a platform
  value rather than a logic divergence — every shipped Claude agent already
  runs at maximum effort, so a justified-high-effort arm would be
  indistinguishable from the immutable production comparator that already
  occupies that role here; the expected twin action, which is none; and the
  resulting status, closed with nothing owed on either side. A reviewer MUST be
  able to reach the sanctioned-divergence conclusion from this section alone,
  without opening either roadmap.
- **FR-035a**: The divergence MUST remain confined to enumeration values. Every
  record shape, required-member set, and member name in the control registry
  and the comparison contract MUST stay mirror-identical, so platform
  differences remain values rather than schemas. The sanctioned-divergence set
  MUST be closed at this one entry: a second divergence, or a divergence
  classified against a contract document, a declared member, a frozen numeric,
  or a decision-semantics entry, MUST fail the FR-034a check. The divergence
  MUST NOT be closed by registering a fourth arm, FR-001 having closed the set.
- **FR-036**: A member the twin declines or cannot mirror MUST be reclassified
  in the record from `mirror_required` to a named reconciliation candidate and
  MUST be appended, in the same change, to a roadmap reconciliation entry of
  the CAR-012 class — CAR-012 / G56R-012 itself where the unmirrorable member
  turns on a contract that pair already covers, otherwise a new paired sibling
  entry raised the way CAR-012 was raised from CAR-003's open coordination
  items. A CAR-004-only item MUST NOT be folded into CAR-012, whose
  dependencies are the two already-merged evaluation specs. The roadmap entry,
  not this record, is the durable tracker, so nothing depends on the handoff
  document being re-read. The member MUST NOT be silently dropped, and it MUST
  NOT be reshaped or weakened on this side to make it mirrorable: that would be
  an in-place edit of a content-addressed control, which FR-002 forbids, and no
  CAR-004 member may be authored into a frozen CAR-003 contract to obtain
  mirroring, which FR-005 forbids. A deferred member remains fully enforced
  here, unchanged.
- **FR-036a**: At publication the reconciliation candidate list MUST be empty
  and MUST say so explicitly rather than leaving an empty list ambiguous:
  G56R-004 has not started, so no member can yet be declared unmirrorable, and
  every entry MUST therefore be `mirror_required` or the single sanctioned
  divergence. A reconciliation candidate is a disposition only the twin owner's
  response can create, and creating one after CAR-004 merges is a normal
  follow-up change that reopens no frozen control identity.
- **FR-037**: CAR-004 MUST NOT block on G56R-004. The complete coordination
  obligations are that the twin-handoff record is committed in the CAR-004
  implementation pull request and that the G56R-004 owner is notified before
  that pull request merges; twin acknowledgment, twin response, and twin
  landing are not merge preconditions, and no CAR-004 artifact may be withheld
  nor any downstream Claude spec deferred awaiting a mirror. The parity
  contract imposes no cross-platform merge gate — its scope is the CAR-001 and
  G56R-001 candidate-route baselines and its only gates constrain manifest
  consumption and source revalidation — and the joint-change rule reaches only
  members verified byte-identical across the two worktrees, which FR-004 and
  FR-005 keep every CAR-004 member outside of. CAR-012 sits off the CAR-004
  through CAR-011 critical path and is required only before an analysis pools
  outcomes across the two platforms, which FR-027 forbids CAR-004 from
  producing.
- **FR-037a**: The record MUST state its publication date and the reference by
  which the G56R-004 owner was notified, so the one real merge precondition is
  verifiable from the artifact itself. If any CAR-004 content address changes
  after the record is written, the record MUST be re-issued with corrected
  digests before merge, so the twin mirrors a pinned state rather than a moving
  branch. The record MUST NOT itself be a hash-relevant input to any control's
  or the comparison contract's content address, so a twin response recorded in
  it can never re-identify a comparator frozen before the answer is known.

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
  Completeness across the mechanically derivable categories is machine-verified
  by re-derivation rather than attested, with zero differences in either
  direction. [FR-034] [FR-034a]
- **SC-013**: CAR-004 merges with the twin-handoff record committed and the
  G56R-004 owner notified, and with zero merge preconditions on twin
  acknowledgment, response, or landing — verifiable from the record and the
  change set alone. [FR-037] [FR-037a]
- **SC-012**: Every control and the comparison contract carry a recorded freeze
  timestamp and a content address in a committed artifact, and an automated check
  recomputes each digest and confirms it matches the recorded one. [FR-002]
- **SC-014**: The adaptive control's `escalation_ladder` carries every admitted
  tuple of its bound successor-capability freeze exactly once, and an automated
  check rejects a duplicate, an omission, a within-model position contradicting
  the frozen effort ladder, and a cross-model step with no recorded rationale.
  [FR-011a] [FR-011b]
- **SC-015**: The multi-child orchestration replay resolves the two
  non-continuous dimensions to exactly one value each — a worst-wins terminal
  state and an acceptance floored to 0 whenever that state is not `completed` —
  with zero null aggregate acceptances in any committed fixture row.
  [FR-016a] [FR-016b] [FR-016c]
- **SC-016**: The per-component margin map is total over all eight frozen Pareto
  dimensions, with four margin-eligible at 0.10 and four declared no-worse-only,
  and a zero-valued comparator component yields `margin_not_computable` rather
  than a dominance verdict. [FR-021] [FR-021a] [FR-021c]
- **SC-017**: The registry's three raw-token smoke bounds sum to exactly
  1,000,000 as a machine-checked identity, and both new contract documents
  validate with no reference resolving outside their own `#/$defs/`.
  [FR-023] [FR-030]

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
- **Numeric values are frozen and their serialization is settled.** The 10%
  relative margin, N = 3, and the smoke caps are settled as decisions, and the
  1,000,000-token and 30-minute ceilings were recorded at moderate confidence.
  The serialization itself is settled here, so Plan and Implement have no latitude
  over placement or values. Two new additive contract documents land under
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`, each with a committed
  frozen instance and each carrying a frozen status, its own identifier and digest
  pair, a `frozen_at` timestamp, and `additionalProperties: false`, following the
  frozen analysis-plan precedent:
  - `policy-control-registry.schema.json` owns the closed-at-three control set and
    everything hash-relevant to a control's identity: each control's execution
    contract, the adaptive control's `escalation_ladder`, the orchestration
    control's topology descriptor and `terminal_state_severity` array, and
    `de_escalation_clean_pass_threshold: 3`. N = 3 lives inside the adaptive
    control's definition rather than in the comparison contract, because it
    changes what that control is and must sit inside its content address.
  - `control-comparison.schema.json` owns the CAR-011-facing rules: the
    eligibility floors, the dominance rule with the per-component margin map
    (keyed on the four margin-eligible dimension names at 0.10 each, with the
    other four declared no-worse-only), the comparator denominator and the
    zero-comparator rule, the dimension-name projection, the single confidence
    method, the multiplicity position, the verdict-to-claim-class mapping, and the
    reserved-partition binding.

  The smoke caps ride the already-frozen budget member names as a `smoke_bounds`
  object in the registry, shared by all three controls and hash-relevant to the
  registry document rather than to any control's identity: `max_attempts: 5` and
  `max_candidates: 1` for five non-reserved objectives at one repetition each,
  `max_confirmation_entries: 0`, `max_duration_seconds: 1800`,
  `max_input_tokens: 800000`, `max_cache_read_tokens: 150000`, and
  `max_output_tokens: 50000`. The three raw-token bounds sum to exactly 1,000,000,
  asserted as an identity so FR-030's ceiling is machine-checked rather than
  prose; `max_cache_write_tokens_by_ttl_class` is declared over the frozen
  `ephemeral_5m` and `ephemeral_1h` classes but stays outside that identity, cache
  write being diagnostic-only and never a Pareto dimension. The smoke MUST NOT be
  serialized as an instance of the frozen CAR-003 experiment-policy document,
  whose branches would force a partition type and an analysis or calibration
  binding CAR-004 may not create, and the new documents MUST NOT reference frozen
  CAR-003 schemas by `$ref`, because the repository validator resolves only local
  `#/$defs/` references and fails closed on anything else; CAR-003 contracts are
  referenced by identifier and digest under FR-004 instead.

  Alpha is adopted from the frozen CAR-003 instance rather than invented: alpha is
  0.05 with a confidence level of 0.95, and the single FR-023 confidence method is
  a one-sided lower confidence bound at that level, clustered by role with
  `cluster_robust_sandwich_variance_by_role`. CAR-011's three predeclared
  secondary control arms form one new multiplicity family,
  `secondary_control_arm_family`, declared in the comparison contract beside and
  disjoint from the three frozen FR-050 families and the guardrail family,
  following the precedent that stood the guardrail family up as an error-control
  concern belonging to none of them; it MUST NOT be added to the frozen analysis
  plan's multiplicity declaration, which is closed at three families. Its
  adjustment is `holm_bonferroni_within_the_secondary_control_arm_family` at a
  family-wise alpha of 0.05. The family draws no alpha from the primary
  comparison, which retains its full 0.05, because a control-arm result can only
  restrict release wording under FR-024 and never license a qualification; cluster
  adjustment remains a precondition rather than a multiplicity control. Every
  numeric in both documents carries its unit and comparison direction, following
  the frozen guardrail method's units and direction precedent, so FR-034 category
  6 is derived from the committed bytes rather than transcribed. The
  1,000,000-token and 30-minute ceilings keep the moderate confidence at which
  they were recorded; serializing them does not upgrade it.
- **Downstream consumers.** CAR-011 applies these contracts; CAR-005 through
  CAR-010 inherit the frozen candidate-set boundary and the reserved-partition
  guard; G56R-004 mirrors the new members; release reviewers read the messaging
  mapping.
