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
    delivered evidence set the guard passes; **And** the smoke plan refuses to
    emit a reserved objective at plan time as well as refusing to seal a record
    that references one. [FR-025] [FR-026] [FR-026a]
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
    members sum to exactly the declared `raw_token_ceiling` of 1,000,000 as a
    machine-checked identity, and every other smoke-bound member carries a frozen
    value; **And** neither document resolves a reference outside its own
    `#/$defs/`; **And** the `secondary_control_arm_family` is declared in the
    comparison contract, disjoint from the frozen analysis plan's three families
    rather than added to them. [FR-004] [FR-023] [FR-030] [FR-030a]
32. **Given** the committed contract documents and their frozen instances,
    **When** every recorded content address is recomputed under the single frozen
    preimage rule, **Then** each control, the registry document, and the
    comparison contract match their recorded digest; **And** changing the freeze
    timestamp alone changes the address, so a re-freeze is a new version rather
    than a silent re-issue. [FR-002a] [FR-002b] [FR-002c]
33. **Given** the CAR-003 bindings a CAR-004 document records, **When** each bound
    document's digest is recomputed from its committed bytes, **Then** every
    binding matches; **And** a seeded byte change to any bound CAR-003 document
    fails the check closed rather than passing unnoticed. [FR-005a]
34. **Given** the reserved CAR-011 entry and the CAR-004 smoke entry, **When**
    they are registered, **Then** each carries a partition type drawn from the
    frozen closed five-member set, the smoke entry is never
    qualification-eligible, both entries record `owning_spec` as `CAR-004`, the
    comparison contract's binding pins the reserved entry's membership digest,
    and a seeded duplicate identifier or shared objective fails registration
    closed. [FR-025a] [FR-025d] [FR-025b] [FR-025c]
35. **Given** a control that has not cleared the eligibility floors, **When** its
    permitted release wording is looked up, **Then** exactly one wording class is
    returned — the same no-comparative-claim class as inconclusive, imposing no
    messaging restriction — and the verdict enum still carries exactly three
    members. [FR-019] [FR-024a]
36. **Given** one evidence row carrying a terminal state, a failure plane, and a
    failure code at once, **When** its policy response is resolved, **Then**
    exactly one response is returned under the declared precedence over the
    closed source set; **And** the retry-count and budget-threshold sources
    FR-008 admits each carry a mapped response and a rank; **And** the plane map
    agrees with the code map under the frozen plane derivation and the
    terminal-state map agrees with it under the frozen candidate-plane pairing.
    [FR-010b] [FR-010c]
37. **Given** a run that exhausts its retry bound and a run that breaches its
    cancellation bound, **When** each objective-level record is produced,
    **Then** each records the frozen terminal state paired with its frozen
    candidate-plane failure code, neither counter was reset by an escalation, and
    the resulting aggregate is non-`completed` with acceptance 0. [FR-014a]
    [FR-016a] [FR-016b]
38. **Given** a platform-initiated route change, **When** the row is resolved,
    **Then** it is identified by the already-frozen `service_reroute` failure
    code rather than a coined signal, resolves to `non_scorable`, leaves the
    escalation allowance and ladder position untouched, neither advances nor
    resets the clean-pass streak, and — inside an orchestration unit — makes the
    whole unit non-scorable. [FR-015a] [FR-012a]
39. **Given** an orchestration unit whose rows each record the node that spawned
    them, containing a nested grandchild and a member that recorded no terminal
    state, **When** the aggregate is produced, **Then** the grandchild is inside
    the unit for both the additive sum and the fan-out ceiling; **And** the
    member with no terminal state makes the row non-conforming and it is refused
    rather than folded over the remainder. [FR-016d] [FR-017a]
40. **Given** the three bounded smokes, **When** each is asked to show it
    demonstrated its behavior, **Then** the adaptive smoke shows the served
    model, effort, and route moving from one declared ladder entry to the next
    across the escalation, the unpinned smoke shows a served model and effort
    equal to the pinned parent session's, and the orchestration smoke shows at
    least two non-parent unit members and a parent wall time strictly below
    their summed wall times; **And** every one of those values is read from the
    evidence the run produced rather than from the dispatch request; **And** a
    smoke lacking its observable is recorded as not demonstrated rather than
    relabeled. [FR-031] [FR-031a]
41. **Given** the adaptive and unpinned smokes, **When** their records are
    audited, **Then** each carries the already-frozen observation that no
    session-level subagent-model override was in force, and a smoke that cannot
    record it true is not reported as demonstrating either behavior.
    [FR-031a]
42. **Given** an orchestration unit whose children consumed cache writes in both
    frozen TTL classes and cache reads, **When** the smoke bounds are checked,
    **Then** the cache quantities are read against the parent-plus-children
    aggregate keyed identically to the declared ceilings; **And** the
    reasoning-token member sums with the other three raw-token members while
    entering no dominance comparison; **And** a member that recorded no cache
    diagnostic makes that bound unobserved rather than passed or zero.
    [FR-016] [FR-016e] [FR-030b]
43. **Given** an orchestration smoke whose children ran concurrently, **When**
    its bounds are evaluated, **Then** all four are counted over the whole unit,
    the 30-minute cap is read as elapsed wall clock rather than as the additive
    duration the Pareto rule sums, and spawning a child consumes no attempt
    against the five-objective allowance. [FR-030b] [FR-014a]
44. **Given** a smoke run whose observed authentication mode is `api_key`,
    **When** it is offered as CAR-004 evidence, **Then** it is refused as
    evidence rather than recorded and kept, and it counts toward neither FR-031
    nor SC-009; **And** the observed `api_key` value is still recorded on the
    refused smoke's own record alongside the refusal, so a refused run stays
    distinguishable from one that never ran;
    **And** the frozen member the mode is recorded through is the Claude-side
    one enumerated `subscription | api_key`, bound by identifier and digest, not
    the shared member enumerated `chatgpt_subscription | api_key`. [FR-030c]
45. **Given** the three smoke arms, **When** cache isolation is evaluated,
    **Then** all three unordered arm pairs record `observed_disjoint` with both
    root digests present; **And** a pair recording `observed_shared` carries the
    frozen infrastructure-plane code while a pair recording `unobserved`
    carries the frozen evidence-boundary code, each invalidating the affected
    smoke; **And** the per-arm ephemeral-root precommitment alone is not
    accepted as the observation; **And** every root is recorded as a digest
    rather than a filesystem path. [FR-032] [FR-032a]

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
  still valid, not an error, because the descriptor's fan-out is a declared
  ceiling rather than an exact count. [FR-016] [FR-017a]
- **Fan-out exceeded**: a run spawns more automatically spawned children than the
  frozen topology descriptor declares. The row does not conform to the control
  and must be refused rather than aggregated; accepting it would charge a larger
  topology's cost to a smaller frozen identity. [FR-017a]
- **Mirrored enum gains or loses a member**: a joint change with the twin changes
  the membership of a frozen CAR-003 enum a CAR-004 map is bound to. The
  set-equality check fails closed and the control is re-frozen as a new version.
  Editing the map in place would leave a signal unmapped inside an unchanged
  content address, and editing the CAR-003 enum is forbidden outright.
  [FR-010a] [FR-005]
- **Ineligible control**: a control never clears the eligibility floors, so the
  procedure stops before producing any verdict. Release wording still resolves to
  exactly one class — no comparative claim, no restriction — rather than falling
  outside the mapping. [FR-019] [FR-024a]
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
- **Non-scorable objective inside a streak**: a platform-initiated route change
  lands between two clean objectives. The objective is excluded from the streak
  entirely — it neither advances nor resets it — so platform behavior can neither
  drive a de-escalation nor block one. [FR-012a] [FR-015a]
- **De-escalation due at the floor**: the streak reaches three while the policy
  sits on the first ladder entry. No step is recorded and no wrap-around to the
  final entry occurs, and the streak still resets, so the policy cannot idle at
  the floor holding a spent streak that fires the instant it escalates.
  [FR-012a] [FR-011b]
- **Bound breached mid-objective**: a run exhausts its retry bound or breaches
  its cancellation bound. It records the frozen terminal state paired with its
  frozen candidate-plane failure code, folds as non-`completed`, and floors
  acceptance to 0. An escalation earlier in the objective does not reset either
  counter. [FR-014a] [FR-016a] [FR-016b]
- **Unit member with no terminal state**: a spawned child records no terminal
  state at all. The row is non-conforming and is refused rather than folded over
  the remaining members, because a skipped member would let a hung child vanish
  from a worst-wins result while its cost was still charged. [FR-016d]
- **Serially dispatched fan-out**: an orchestration smoke spawns its children one
  after another. The parent's wall time is then at least the sum of the
  children's, the parallel observable is not satisfied, and the run is recorded
  as not demonstrating a parallel dispatch — it is not relabeled, and the
  aggregation half passing does not make up for it. [FR-031a]
- **Wall time missing on a unit member**: the parent or one of the compared
  members records a null wall time. The parallel inequality is undecidable, so
  the smoke is recorded as not demonstrating a parallel dispatch; the missing
  value is never read as zero, which would have made the inequality trivially
  true and inverted the check. [FR-031a]
- **Escalation requested but not served**: the adaptive smoke sets its declared
  dispatch-time parameter and the post-escalation attempt still reports the
  previous ladder entry's model and effort. The demonstration fails on the
  read-back rule, because what the request asked for is not evidence.
  [FR-031a]
- **Subagent-model override in force**: the smoke environment cannot record the
  frozen no-override observation as true. Neither the adaptive nor the unpinned
  smoke may be reported as demonstrating its behavior, because the served model
  would be decided by the override rather than by the declared parameter or the
  parent session. [FR-031a]
- **Unrecorded cache diagnostic on one unit member**: a child records no cache
  diagnostic. The affected aggregate is not computable, so the bound it feeds is
  recorded unobserved rather than passed, and the missing value is never read as
  zero — a softer disposition than a missing terminal state gets, because it
  leaves a bound unproven rather than the unit malformed. [FR-016e]
- **Two arms sharing a cache root**: a pair's roots are not disjoint. The pair
  records `observed_shared` under the frozen infrastructure-plane code and the
  affected smoke stops being FR-031 evidence, rather than the breach being noted
  and the run kept. [FR-032a]
- **Cache state unobservable**: a pair's roots cannot be shown distinct at all.
  This is an evidence-completeness failure under the frozen evidence-boundary
  code, deliberately not classified as a confirmed breach, and the affected
  smoke is equally not FR-031 evidence. [FR-032a]
- **API-key authentication observed mid-series**: one smoke turns out to have run
  under an API key. It is refused as evidence rather than recorded and kept, so a
  run the supported path does not require can never stand as evidence for the
  requirement that keeps the path free of one. The observed mode is still
  recorded on the refused record, and the remedy is a re-run on the subscription
  path rather than a relabel. [FR-030c]

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
- **FR-002a**: Every CAR-004 content address MUST be produced by one preimage
  rule, adopted from the frozen CAR-003 digest primitive rather than coined
  here: SHA-256 over the canonical JSON serialization of the record — sorted
  keys, minimal separators, no NaN, UTF-8 — with the record's own digest member,
  and only that member, removed from the preimage. Declared array order is
  preserved and never sorted, as FR-011b already requires for the ladder.
  Stating the rule at requirement level is what makes "recompute the digest and
  compare" a decidable check rather than an implementation choice, and reusing
  the frozen primitive keeps one preimage rule across the program instead of two
  that can silently disagree.
- **FR-002b**: The freeze timestamp MUST be hash-relevant — inside the content
  address, not merely recorded beside it — so that re-freezing an otherwise
  identical definition at a different instant is a new version rather than a
  silent re-issue of the same identity, and it MUST be a `Z`-suffixed UTC
  instant. "Alongside" in FR-002 fixes where the timestamp is stored, never that
  it is excluded from the preimage.
- **FR-002c**: The control-registry document and the comparison contract MUST
  each additionally carry their own recorded content address computed over the
  whole document under FR-002a. Control-level addresses alone would leave every
  registry-level hash-relevant member outside any content address — the closed
  control array, the shared smoke bounds, and the CAR-003 binding set — so a
  change to one of those would not surface as a new version.
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
- **FR-005a**: Every CAR-003 binding a CAR-004 document records MUST be
  verified rather than merely declared: an automated check MUST recompute each
  bound document's digest from its committed bytes and MUST fail closed when the
  recomputed value differs from the recorded one. The digest meant here is the
  SHA-256 of the document's committed bytes, the same document-level digest
  FR-034 category 1 records — not the FR-002a record preimage, which addresses a
  record's fields rather than a file's bytes. The two rules govern different
  objects and neither substitutes for the other. Without this check the binding
  is decorative — an edit to a frozen CAR-003 document, the exact thing FR-005
  forbids, would pass CAR-004's own suite unnoticed and leave SC-004 resting on
  reviewer diff vigilance alone.

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
- **FR-010a**: Every CAR-004 member required to be set-equal to a frozen CAR-003
  enum — the three signal-to-response maps and the orchestration control's
  `terminal_state_severity` array — MUST have that set equality revalidated on
  every load, and a membership change on the frozen side, a member added or
  removed by joint change with the twin, MUST fail the check closed. The remedy
  is a new control version re-frozen against the changed enum under FR-002; the
  map MUST NOT be edited in place inside the existing identity, and the frozen
  CAR-003 enum MUST NOT be edited to restore agreement, which FR-005 forbids.
  FR-016a already refuses a silent reordering; this refuses a silent membership
  change, which would otherwise leave a signal unmapped or a response orphaned
  inside a content address that never moved.
- **FR-010b**: One evidence row carries a terminal state, a failure plane, and a
  failure code at the same time, so FR-010's per-signal totality does not by
  itself yield one response per row. The adaptive control MUST therefore declare
  a `signal_precedence` — an ordered array over a closed source set, carried as a
  hash-relevant member of its frozen definition — and a row's response MUST be
  the response of the first source in that order whose value is not the frozen
  `none` sentinel, with terminal state ranked last and always valued so every row
  resolves. The closed source set MUST cover every source FR-008 admits: failure
  code, failure plane, terminal state, retry count, and raw-token/duration budget
  thresholds. The last two are declared as ordered `{member, direction,
  threshold}` entries whose mapped response applies once the declared direction
  and threshold are met, so no signal FR-008 admits can be observed without a
  mapped response and a rank. A source FR-008 admits but the precedence array
  omits MUST fail the well-formedness check closed rather than being silently
  unreachable.
- **FR-010c**: The enum-keyed response maps MUST additionally be proven mutually
  consistent against the frozen derivations, because neither the failure plane
  nor a candidate-plane terminal state is independent of the failure code:
  1. **Plane agrees with code** — the frozen contract derives a row's failure
     plane from its failure code rather than authoring the plane beside it, so
     the plane map MUST assign each plane the same response the code map assigns
     to every code on that plane. Codes on one plane that disagree MUST fail the
     check closed. Without this rule the plane map is unreachable and therefore
     decorative: under any code-first precedence it can never decide a row,
     because a `none` code always carries a `none` plane.
  2. **Candidate terminal state agrees with code** — the frozen contract pairs
     each non-`completed` terminal state with exactly one candidate-plane failure
     code, so the terminal-state map MUST assign each such state the same
     response the code map assigns to its paired code.

  Both rules are revalidated on every load under FR-010a. A disagreement is
  repaired by re-freezing the control as a new version under FR-002 — never by
  editing a map in place inside an unchanged identity, and never by editing the
  frozen CAR-003 derivation or pairing, which FR-005 forbids.

  Rule 1's per-plane uniformity is a constraint this feature declares rather than
  one a frozen contract imposes, so it is recorded here with the refinement it
  forecloses. It is bound to the response enum's granularity: the policy
  responses are closed at three coarse members — `escalate`, `hold`, and
  `non_scorable` — and the frozen contract already draws the scorable line at
  plane granularity, admitting the `non_scorable` disposition only on a plane
  other than `none` and `candidate` while keeping candidate-plane terminal
  outcomes as estimand-retained records carrying acceptance 0. `escalate`
  therefore belongs to the candidate plane and to no other, and every remaining
  plane names a condition that reports on the harness, the fixtures, the scorers,
  or the evidence rather than on the route the policy chose. No plane in the
  frozen taxonomy carries codes that want different members of a three-member
  response enum.

  What uniformity forecloses is per-code refinement inside a plane — giving
  `candidate_cancelled` a different response from `candidate_failed`, or letting
  `candidate_budget_exhausted` `hold` where the other candidate codes escalate.
  That refinement is refused, and it MUST NOT be reintroduced by re-freezing a
  control under FR-002, because the constraint is structural rather than
  version-scoped: a control version that broke uniformity would leave the plane
  map unreachable and unchecked again, which is the failure rule 1 exists to
  prevent. If a later consumer needs the policy to separate two codes on one
  plane — CAR-011 is the only consumer in view — the remedy is a change to the
  response mapping's key structure in the control contract, raised jointly with
  G56R-004 so the twin's mirror moves with it, never an in-place divergence
  inside a plane.

  The frozen contract's one intra-plane refinement is not a counterexample to
  this. The frozen disposition binding sends `schema_invalid` to `gate_failed`
  and `binding_digest_mismatch` to `non_scorable` while both sit on the `schema`
  plane, but that split decides whether a malformed record can be scored at all,
  not what the policy should do next, and both codes still resolve to the same
  `non_scorable` policy response here.
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
- **FR-012a**: The clean-pass streak MUST carry a declared accounting rule as a
  hash-relevant member of the adaptive control's definition. N = 3 alone does not
  say which objectives count, when the counter resets, or what happens at the
  ladder floor, and each of those decides whether the policy can oscillate:
  1. **Clean pass defined against frozen members** — an objective counts as a
     clean pass only when its terminal state is `completed`, its failure code is
     `none` (and therefore its failure plane is `none`), its retry count is zero,
     and no declared budget trigger was met. The bar is the declared *trigger*,
     not a budget *breach*: a trigger that fired is evidence the route was
     strained, and it is the same threshold the policy escalates on, so an
     objective that fired one cannot also be the evidence for stepping back down.
  2. **An escalating objective is never clean** — an objective in which the
     policy escalated MUST NOT count toward the streak, so the clean run that
     licenses a step down is always measured at the route the policy moved to,
     never at the route it left.
  3. **A non-scorable objective is excluded** — an objective whose row resolves
     to the `non_scorable` response neither advances nor resets the streak. It is
     not evidence about the policy in either direction: counting it clean would
     let platform behavior drive a de-escalation, and resetting on it would let
     platform behavior block one, and FR-015 refuses both readings. This
     exclusion takes precedence over rule 1 and over FR-012's reset-on-non-clean
     rule: a non-scorable objective is neither a clean pass nor a streak-breaking
     non-clean one, and the streak resumes across it unchanged.

     Exclusion rather than reset is settled by what FR-015 already decided, not
     by preference between two readings. FR-015 refuses to let a
     platform-initiated route change be recorded or counted as a policy
     escalation, which is a statement that platform behavior is not evidence
     about this policy; a streak that reset on such an objective would let the
     platform decide when a de-escalation may not happen, the same contamination
     as counting it clean and only in the opposite direction. Exclusion is the
     unique accounting under which a non-scorable objective moves the policy's
     state in neither direction. It is also the treatment the frozen program
     already gives this evidence rather than a disposition CAR-004 invents: a
     `non_scorable` score bundle is not an accepted estimand record, while a
     candidate-plane terminal outcome — the failing objective that legitimately
     breaks a streak — is retained with acceptance 0.

     The exclusion MUST NOT be silent, matching the frozen attrition policy's
     refusal of complete-case filtering. Every excluded objective is itself a
     committed evidence row carrying the `non_scorable` response and its frozen
     failure code, so a streak that spans excluded objectives stays auditable
     from the committed rows instead of having to be reconstructed, and the
     FR-028 replay fixtures MUST include a streak that both survives an excluded
     objective and completes across it, so the accounting is proven rather than
     asserted.
  4. **The streak resets whenever de-escalation is evaluated** — reaching three
     resets the counter to zero at that boundary whether or not a step actually
     occurs, so one run of three clean passes licenses at most one downward step
     rather than a further step at every subsequent boundary.
  5. **Floor behavior mirrors the ceiling** — a de-escalation that comes due at
     the first ladder entry records no de-escalation and MUST NOT wrap around to
     the final entry, exactly as FR-011b refuses wrap-around at the ceiling. The
     streak still resets under rule 4, so the policy cannot idle at the floor
     holding a spent streak that fires the instant it escalates.

  With FR-011's one-escalation ceiling these rules bound movement to at most one
  step up per objective and at most one step down per three clean objectives,
  which is the guarantee the "streak interrupted" edge case asserts.
- **FR-013**: Every route the adaptive policy can escalate or de-escalate to MUST
  lie inside the frozen candidate set, and a route outside that set MUST be
  unreachable by construction rather than merely discouraged.
- **FR-014**: The adaptive control MUST declare explicit retry and cancellation
  bounds that a deterministic replay can prove were respected.
- **FR-014a**: Every control's retry and cancellation bounds MUST additionally
  declare the scope they are counted over and the outcome of a breach. Without
  both, "a deterministic replay can prove they were respected" is not decidable
  and the FR-016a fold has no defined input on a breached run:
  1. **Scope** — both bounds are counted per objective, spanning every attempt
     and every route the policy occupies inside that objective. An escalation
     MUST NOT reset either counter, so a control cannot buy extra attempts or
     extra wall clock by stepping up.
  2. **Unit scope for the orchestration-changing control** — both bounds are
     counted over the parent-plus-children unit as a whole, matching the additive
     aggregation FR-016 already requires, so a run cannot stay inside its bounds
     by distributing retries or elapsed time across children.
  3. **Breach outcome** — each control MUST declare, as a hash-relevant member,
     the terminal state each bound breach records, drawn from the frozen
     six-member terminal-state enum and paired with its frozen candidate-plane
     failure code under the frozen pairing rather than a coined one. The frozen
     values are `cancelled` with `candidate_cancelled` for a cancellation-bound
     breach — the breach action is a cancellation the harness itself performs,
     which is what the frozen trace's completed-cancellation evidence records,
     while `timed_out` stays reserved for a platform-side timeout the harness did
     not request — and `failed` with `candidate_failed` for a retry-bound breach,
     since exhausting retries means at least one attempt failed, while
     `abandoned` stays reserved for work given up with no recorded failure.

     Representability, not preference, settles this pair. Every score bundle
     carries an execution-trace binding among its required provenance members, so
     a declared breach outcome must be provable against the bound CAR-003
     execution trace, and that trace's terminal-state enum admits only four
     members: `completed`, `failed`, `cancelled`, and `abandoned`. `timed_out`
     and `budget_exhausted` exist only in the score bundle's resource vector, so
     neither can be evidenced on the artifact the replay proves the bound
     against; a control declaring one would freeze an outcome its own replay
     could never demonstrate. Among the three non-`completed` members the trace
     does admit, the trace itself fixes which evidence each one requires —
     `cancelled` requires completed cancellation evidence carrying an enumerated
     reason, which is exactly what a harness-performed cancellation produces;
     `failed` requires at least one failed attempt, which is exactly what an
     exhausted retry bound produces; and `abandoned` requires abandoned work with
     neither a completed cancellation nor a recorded failure, which neither
     breach produces. Each bound therefore has exactly one representable outcome.
     The candidate pairing is equally frozen rather than chosen: the candidate
     plane admits one code per terminal state, and a candidate-plane row whose
     terminal state and failure code disagree is refused.

     Two alternatives are refused explicitly. `timed_out` for the
     cancellation bound is attractive because the bound is expressed as a
     duration, but the trace cannot express it, and the frozen taxonomy reserves
     it for a platform-side timeout the harness did not request, whereas a
     harness cancelling on its own declared bound is a requested cancellation.
     `budget_exhausted` for the retry bound is attractive because the frozen
     budget object carries a `max_attempts` member, but the same
     representability objection applies, and the retry bound is a
     control-declared FR-014 bound rather than the campaign budget the frozen
     experiment policy governs. Both refusals also fail safe on the FR-016a fold:
     `cancelled` outranks `timed_out` in the frozen severity order, so the chosen
     outcome cannot make a breached run fold cleaner than the refused alternative
     would have. The choice never reaches the adaptive response, because both
     outcomes sit on the `candidate` plane and FR-010c.1 requires that plane to
     carry a single response; it changes only the FR-016a aggregate severity and
     the FR-021b terminal-state comparison, each of which is recorded rather than
     inferred.
  4. **Replay covers the breach** — the committed replay fixtures MUST exercise
     both breach paths and not only the respected path. Both breach states are
     non-`completed`, so the same fixtures prove FR-016a folds them by severity
     and FR-016b floors the unit's acceptance to 0.
- **FR-015**: A platform-initiated route change MUST be classified as
  non-scorable and MUST NOT be recorded or counted as a policy escalation.
- **FR-015a**: The observable that identifies a platform-initiated route change
  MUST be the already-frozen failure code `service_reroute`, whose plane the
  frozen contract derives as `treatment` and whose frozen non-scorable
  disposition reason is `service_reroute_requested_route_non_scorable`. No new
  signal, field, or code is coined, so FR-008's binding rule and FR-009's
  no-new-telemetry rule both hold. Leaving the trigger unnamed would make FR-015
  the one policy rule whose input the implementation picks, and a rule keyed on
  an unbound observable cannot be mirrored or replayed. Such a row MUST resolve
  to the `non_scorable` response under FR-010b, and:
  1. it MUST NOT consume the objective's one escalation allowance and MUST NOT
     change the current ladder position, so platform behavior can never spend a
     policy step;
  2. it is excluded from the clean-pass streak under FR-012a.3;
  3. for the orchestration-changing control, a `service_reroute` on the parent or
     on any member of the aggregation unit makes the whole unit non-scorable.
     The unit is attributed at policy level under FR-018 and
     `terminal_state_severity` carries no non-scorable member, so a rerouted
     member cannot be folded away;
     scoring the remainder would report policy behavior for a unit containing
     work the policy did not choose.

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
  acceptance. FR-016b's floor outranks this allowance wherever the two meet:
  when the aggregate terminal state is any member other than `completed`,
  acceptance is 0 whether or not the oracle ran, so null is reachable only on a
  `completed` unit whose oracle did not run. Stating the precedence is required
  because the two
  rules otherwise collide on the common case rather than a corner one — a unit
  that failed and therefore never reached its oracle satisfies FR-016b by
  recording 0 and FR-016c by recording null, and two conforming implementations
  would then disagree on identical evidence.
- **FR-016d**: The membership of the aggregation unit MUST be decidable from the
  frozen record rather than from the phrase "automatically spawned", which names
  no member and admits no check:
  1. **Membership** — the orchestration-changing control MUST declare, among the
     FR-003 evidence rows a valid run must produce, that every non-parent row
     records the identifier of the node that spawned it. The unit is then the
     parent objective's node together with the transitive closure of that
     recorded link, however the node was requested. Descendants below the first
     generation are inside the unit, so a topology cannot shed cost by nesting a
     child one level deeper, which is the same artificial-cheapness failure
     FR-016 exists to prevent. This is a declared evidence requirement of a
     CAR-004 control, hash-relevant under FR-002, and not a telemetry addition.

     The link is authored at dispatch rather than read back afterwards. The
     component that issues a child dispatch records the spawning node's
     identifier on the resulting row at the moment it issues it, which is why
     FR-009 holds: no telemetry field is added and none is read.

     The rationale is that the link is *authored*, not that no spawn structure
     exists to read. Two different frozen contracts are involved and they MUST
     be kept apart, because the rationale is mirrored as an FR-034 category 7
     entry and a twin that conflates them would implement against a member the
     wrong contract carries:

     - The **shared treatment-record contract** — the one the frozen
       Claude-side CAR-003 runner binds unmodified through the shared
       treatment-trace authority — *does* publish a required
       `parent_child_graph` on every treatment trace: a root, a nullable
       parent, and a child set, all as execution-trace identifiers. Its
       reciprocity, acyclicity, and root agreement are already enforced by the
       shared treatment-trace bundle validator, not by a CAR-004 check and not
       by a Claude-only one. A twin implementing against "there is no graph"
       would conclude this contract lacks a member it in fact requires.
     - The **CAR-002 Claude trace contract**, by contrast, publishes only a
       nullable parent-session configuration string on its route-resolution
       record and no spawn structure at all. Nothing in CAR-004 may read a
       spawn graph out of it.

     What the shared graph is not, either way, is a platform telemetry
     emission: whatever component writes a trace writes its graph, so a unit
     boundary rested on it would still be resting on the harness's own
     authorship, one indirection further from the dispatch that knows the
     answer. That is why the CAR-004 unit boundary is authored at dispatch even
     though a graph exists to read.

     **Agreement with the frozen graph.** Wherever a unit member's evidence
     binds a frozen execution trace carrying the shared contract's
     `parent_child_graph`, the
     CAR-004 unit boundary MUST agree with it: the graph's child set and the
     authored spawn links MUST induce the same membership, and a disagreement
     MUST fail the row closed rather than letting either source win. Two
     records of one run that disagree about who spawned what leave the unit
     undecidable, which is the same failure rules 3 and 4 close from the other
     direction. The obligation is conditional on the binding existing because a
     CAR-004 replay case need not bind a full execution trace; where no such
     binding exists the authored links stand alone and nothing is inferred.

     Dispatch authorship also fixes what this rule can require, which the FR-031
     live smoke makes concrete. A harness can record only the dispatches it
     issues, so the orchestration-changing control's frozen child shape MUST
     declare a dispatch mechanism under which every unit member is dispatched
     through the CAR-004 harness, and a topology admitting a member that could
     spawn a further node outside that harness is not freezable under CAR-004,
     because its membership would not be decidable from the record. With that
     declaration the FR-031 smoke is feasible on the supported subscription path
     by construction: the smoke issues the real parallel dispatch itself and
     therefore holds each child's spawning identity at the moment of dispatch,
     with nothing to recover from platform telemetry afterwards. The rule
     therefore holds without any change to the frozen contracts, and it MUST
     NOT be satisfied by inferring parentage from timing, ordering, or session
     identifiers, none of which the frozen record makes decidable.
  2. **Fan-out counts the whole unit** — the FR-017a fan-out ceiling is read
     against every unit member other than the parent, for that same reason.
  3. **A member with no terminal state fails closed** — a unit member recording
     no terminal state at all makes the row non-conforming, and it MUST be
     refused rather than folded over the remaining members. A worst-wins fold
     that skipped such a member would let a hung or unreported child disappear
     while its parent still reported `completed` and its cost was still charged.
     This is deliberately the opposite disposition to FR-016c's null acceptance:
     a null acceptance is a reportable evidence gap on an otherwise well-formed
     unit, whereas a missing terminal state leaves the unit's severity undefined
     and therefore malformed.
  4. **A member with no authored spawn link fails closed** — a row that is
     neither the parent's own nor carries an authored spawning identifier makes
     the run non-conforming and MUST be refused rather than aggregated, the same
     disposition rule 3 gives a member with no terminal state. A run that
     produced work it cannot attribute has an undecidable unit boundary, and
     folding the attributable remainder would charge a partial cost to a frozen
     identity — the artificial-cheapness failure again, arriving through an
     unattributed member rather than a nested one.
- **FR-016e**: "The complete raw token vector" MUST resolve to a named member
  set rather than to a phrase, and the quantities the smoke bounds constrain but
  the Pareto rule never reads MUST carry an aggregation rule of their own.
  FR-016 otherwise leaves two different sets — the frozen four-member raw token
  vector and the frozen eight-dimension Pareto resource vector — behind one
  word, and leaves the cache quantities `smoke_bounds` declares ceilings on with
  no rule at all, so a unit could breach a declared ceiling while reporting
  compliance:
  1. **The raw token vector is the frozen four** — `input_tokens`,
     `output_tokens`, `cached_input_tokens`, and `reasoning_output_tokens`, the
     closed member set of the frozen CAR-002 raw-token vector. All four sum
     across the parent and every unit member. That set is deliberately not the
     frozen Pareto resource vector: the two overlap on three token members, the
     Pareto vector adds `duration_ms`, `retries`, `compactions`, `acceptance`,
     and `terminal_state`, and the raw vector adds `reasoning_output_tokens`,
     which the Pareto vector does not carry. FR-016's two phrases therefore name
     two sets and the aggregate MUST satisfy both.
  2. **Reasoning tokens aggregate but stay non-decision-bearing** — the frozen
     contract requires a reasoning-token report on every attempt while fixing it
     as never decision-bearing, so the unit carries the unit-level sum and that
     sum MUST NOT enter the dominance comparison. Summing it is what keeps the
     unit's recorded cost honest; admitting it to the comparison would add a
     ninth dimension to a frozen eight-dimension policy, which FR-005 forbids.
  3. **Cache write by TTL class and cache read aggregate additively** — both sum
     across the parent and every unit member, cache write summed per TTL class
     over the frozen closed key space (`ephemeral_5m`, `ephemeral_1h`) so the
     aggregate is keyed identically to the ceiling that bounds it. The FR-030
     bound check for these members MUST be read against the unit aggregate, not
     against the parent's own consumption, which is the only reading under which
     the declared ceilings bound what the run actually spent.
  4. **Aggregating them promotes nothing** — the cache quantities remain
     diagnostic-only. They MUST NOT become Pareto dimensions, MUST NOT enter the
     FR-030a raw-token identity, and MUST NOT be constrained against
     `max_input_tokens`. The frozen contract states their diagnostic-only status
     as a consequence of the raw-token vector being closed, and an aggregate
     cannot change what the member is.
  5. **An unrecorded member fails to unobserved, never to zero** — the frozen
     cache diagnostic admits null values, so a unit member that recorded no
     cache diagnostic makes that quantity's aggregate not computable. The bound
     check for it MUST then be recorded unobserved rather than passed, and MUST
     NOT treat the missing value as zero. This is deliberately a softer
     disposition than FR-016d.3 gives a missing terminal state: a missing
     diagnostic leaves a bound unproven, while a missing terminal state leaves
     the unit's severity undefined and therefore the row malformed.

  Each of the five is an FR-034 category 7 decision-semantics entry, because
  none of them adds a schema member to a frozen contract and two conforming
  implementations must fold identical evidence the same way.
- **FR-017**: The orchestration-changing control MUST carry a content-addressed
  topology descriptor as part of its frozen identity.
- **FR-017a**: The topology descriptor MUST be restated in full inside the
  control's frozen definition as exactly three members — a topology identifier,
  a declared fan-out, and a child shape — so SC-002's "altering any hash-relevant
  field" is decidable over an enumerated member set rather than an open one.
  Fan-out MUST be read as a declared ceiling on automatically spawned children
  rather than an exact count: a run that spawns fewer children, zero included,
  still conforms to the frozen identity and yields a valid row, which is what the
  zero-child edge case requires. A run that spawns more children than the
  declared fan-out does not conform to the control and MUST be refused rather
  than aggregated, so a run cannot exceed the frozen topology while its cost is
  still charged to that control.
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
- **FR-024a**: The FR-019 eligibility-floor outcome produces no member of the
  verdict enum at all, so a mapping total over dominant, not-dominant, and
  inconclusive does not by itself cover every outcome the frozen decision
  procedure can reach. The comparison contract MUST therefore map that
  no-verdict outcome explicitly onto the same no-comparative-claim wording class
  as inconclusive and MUST impose no messaging restriction for it. That mapping
  MUST be declared inside the eligibility-floor block, beside the member that
  already records the no-verdict result, rather than as a fourth row of the
  verdict-to-claim-class map. The hole MUST NOT be closed by adding a fourth
  member to the verdict enum or a fourth entry to the messaging map, either of
  which would change a declared shape the twin mirrors; it is a declared outcome
  of the eligibility stage, not a verdict. The claim-class lookup is then
  total over every reachable outcome rather than only over the three verdict
  states, so a release reviewer facing an ineligible control is never left
  without a permitted wording class.

#### Reserved comparison partition

- **FR-025**: A named comparison partition reserved for CAR-011 MUST be declared
  in the existing corpus/partition registry with content-addressed membership.
- **FR-025a**: Both new registry entries MUST take a member of the frozen closed
  five-member partition-type set; no new type may be coined, FR-005 having closed
  that enum against extension. The reserved CAR-011 comparison partition is
  registered as `integrated_confirmation` and qualification-eligible; the CAR-004
  smoke partition is registered as `calibration` and never qualification-eligible
  — a pairing the frozen builder already refuses to invert — so CAR-004's smoke
  evidence is structurally incapable of carrying qualification-bearing rows under
  FR-027 rather than merely instructed not to.
  Registering a qualification-eligible partition CAR-004 may not consume is the
  frozen precedent rather than a new liberty. The CAR-003 calibration pilot
  registers four reserved qualification-eligible partitions — screening,
  selection, cohort-lock, and integrated-confirmation — that the pilot itself
  never consumes, for the stated reason that registering them is what turns "no
  such objective was consumed" from a claim into a check the run performs
  (`tests/speckit-pro/layer6-efficiency/run-calibration-pilot.py:395-425`).
  Registering is not consuming, and registration is what makes FR-027 decidable:
  the frozen consumption path admits an objective only when it belongs to a
  `calibration` partition carrying `qualification_eligible: false`
  (`tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py:331-365`),
  so an unregistered reserved objective would be refused as unregistered rather
  than as reserved, and the reservation would carry no membership digest for
  FR-025c to pin.
- **FR-025b**: Both entries MUST be registered through the frozen registration
  path so that objective-level disjointness is enforced mechanically, against
  each other and against every already-registered partition, and a duplicate
  partition identifier, a shared objective identifier, or a membership digest
  that does not match its preimage MUST fail closed. Declaring the reserved set
  without registering it would rest "held untouched" on the FR-026 guard alone
  and would let one objective silently belong to two partitions.
- **FR-025c**: The comparison contract's binding to the reserved partition MUST
  pin that entry's partition identifier together with its membership digest —
  the digest over the deduplicated, lexicographically sorted objective
  identifiers — because only that digest pins membership. Binding any other
  digest would let the reserved set's contents change while the binding still
  verified, which is the failure this reservation exists to prevent.
- **FR-025d**: Both entries MUST record `owning_spec` as `CAR-004`, the spec that
  freezes them, matching that same precedent — the pilot's four reserved entries
  all carry `owning_spec: "CAR-003"` even though CAR-003 consumes none of them.
  `owning_spec` is provenance, not authority: no frozen admission rule reads it,
  the beneficiary of the reservation is carried by the partition identifier and
  by the FR-025c binding, and recording a not-yet-started spec there would assert
  an ownership CAR-004 cannot confer on that spec's behalf and that nothing
  checks. CAR-011 later binds the entry by identifier and membership digest under
  its own spec; it inherits no obligation from this field.
- **FR-026**: An automated guard MUST fail if any CAR-004 replay row or smoke row
  references a member of the reserved partition, and MUST pass on the delivered
  evidence set.
- **FR-026a**: The guard MUST have a stated enforcement point on both halves.
  The replay half runs in the committed suite together with the seeded-violation
  case. The smoke half cannot run there: FR-033 keeps per-run smoke output out of
  version control, so no committed suite run can ever read a smoke row. The smoke
  half MUST therefore be enforced at the two points an operator actually touches:
  1. **Plan time** — the printed smoke plan MUST derive its objective list from
     the registered CAR-004 smoke partition and MUST refuse to emit any objective
     the frozen consumption path does not admit, so an operator is never handed a
     reserved objective to run.
  2. **Seal time** — sealing MUST be refused when any row of the produced record
     references a reserved objective identifier.

  Naming only the committed half would leave the smoke obligation unenforceable
  in practice while still reading as covered, and naming only the seal would let
  an operator who declines to seal bypass the guard outright. With the plan-time
  refusal in place, declining to seal withholds evidence rather than evading a
  check: the run yields no admissible record, satisfies neither FR-030 nor
  FR-031, and proves nothing. The residual — an operator who ignores the printed
  plan, hand-runs a reserved objective, and never seals — is beyond what any
  repository check can observe, because FR-033 and the developer-local assumption
  keep that run's output untracked. It is bounded rather than ignored: the frozen
  registry path admits only ineligible `calibration` objectives, so every
  reserved objective is refused wherever the frozen machinery is used at all, and
  the residual is recorded here rather than left implied.
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
- **FR-030a**: The 1,000,000 raw-token ceiling MUST be recorded in the registry
  as its own declared member carrying its unit and comparison direction, and the
  machine-checked identity MUST be asserted against that member — the three
  raw-token sub-budgets sum to exactly the declared ceiling — rather than against
  a literal that appears only in prose. FR-034 category 6 is derived from the
  committed bytes, so a ceiling existing only as the sum of three other members
  could not be derived at all and would have to be transcribed, which FR-034a
  forbids. Every other member of the smoke bounds MUST likewise carry a frozen
  value; none may be left for Implement to choose, because the object is
  hash-relevant to the registry's content address.
- **FR-030b**: Each smoke bound MUST declare the scope it is counted over.
  FR-014a already fixes unit scope for the retry and cancellation bounds, while
  FR-030 alone scopes none of its own four, and on the orchestration-changing
  control an unscoped bound is not a bound: concurrent children could each
  consume a full ceiling while every individual node stayed inside it.
  1. **The unit is the counting scope** — all four bounds are counted over the
     parent-plus-children unit as a whole, the same unit FR-014a.2 fixes and
     FR-016d defines, so a run cannot stay inside a ceiling by distributing
     spend across children.
  2. **Token and cache ceilings read the aggregate** — the raw-token ceiling and
     the cache ceilings are read against the FR-016e unit aggregate.
  3. **The wall clock is elapsed, not additive** — the 30-minute bound is
     elapsed wall clock over the unit, from the parent's dispatch to the last
     member's completion. It is deliberately not the additive `duration_ms`
     the frozen Pareto rule reads and FR-016 sums: a parallel unit legitimately
     records an additive duration larger than its elapsed time, and both are
     recorded. Conflating them would either stop a compliant smoke early or let
     a serial one overrun.

     This assigns the shared frozen budget member no second reading. The bound
     is carried by the frozen budget's `max_duration_seconds`, and CAR-003's own
     ledger already evaluates that member against monotonic elapsed time
     measured once across the whole run rather than against any sum of
     per-attempt durations, stopping at the first ceiling reached. The additive
     quantity is a different member entirely — the per-trace wall time the
     Pareto vector reads as `duration_ms` — so the two readings attach to two
     names, and CAR-004 inherits CAR-003's reading of the one they share rather
     than redefining it. What CAR-004 adds is only the *scope* the elapsed
     measurement is taken over, which FR-030b exists to fix and which CAR-003
     never had to state because it had no parent-plus-children unit.
  4. **A child dispatch is not an attempt** — `max_attempts: 5` and
     `max_candidates: 1` express five non-reserved objectives at one repetition
     each, so an attempt is an objective attempt and spawning a child consumes
     none. The number of children is bounded instead by the frozen topology
     descriptor's declared fan-out under FR-017a, which is where a topology's
     size is already governed; counting children as attempts would let the
     topology silently reduce the objective count.
- **FR-030c**: The recorded authentication mode MUST be constraining rather than
  merely observable, and the frozen member it is recorded through MUST be
  identified:
  1. **Which frozen member** — the `authentication_mode` FR-030 names is the
     Claude-side frozen member whose enumeration is exactly `subscription` and
     `api_key`, bound by identifier and digest under FR-004 and re-verified
     under FR-005a. It is explicitly not the shared environment-contract member
     of the same name, whose enumeration is `chatgpt_subscription` and
     `api_key`: recording a CAR-004 smoke against that member would make its
     mode incomparable with every CAR-003 record on this platform. Naming the
     field without its owning contract does not identify it, because the
     repository carries frozen members of that name whose enumerations differ.
     That two-member enumeration is revalidated set-equal on every load on the
     same terms FR-010a fixes for the members it names — this extends that
     discipline to a further member rather than reopening FR-010a's list — and a
     membership change on the frozen side fails the check closed rather than
     being absorbed. Pinning this side of the divergence is not a CAR-004
     invention: the design concept's 2026-07-27 revision names the enumeration
     `subscription | api_key` when it fixes the smoke's authentication path, and
     both frozen Claude-side documents carrying the member declare exactly that
     pair.
  2. **Observed, not intended** — the recorded value is an observation of the
     run that happened, never a restatement of operator intent, a configuration
     setting, or a product-plan claim, matching the PRD's
     recording-without-plan-claims obligation. The frozen Claude-side capability
     library already derives the mode this way, from the observed environment
     rather than from a declaration, so "observed" has a settled meaning here
     rather than a CAR-004-local one.
  3. **Constraining** — a smoke whose observed mode is `api_key` is not valid
     CAR-004 evidence: it MUST be refused as evidence rather than recorded and
     kept, and it MUST NOT be counted toward FR-031 or SC-009. CAR-003 made the
     same field constraining by blocking scoring on a divergence; a CAR-004
     smoke produces no score, so the constraint attaches to the smoke's
     admissibility as FR-031 evidence instead. Without this the smoke could be
     run under an API key, record that fact accurately, and still stand as
     evidence for a requirement that exists to keep the supported path free of
     one.

     **What is refused is admissibility, not the observation.** The observed
     `api_key` value MUST still be recorded on the refused smoke's own record,
     together with the refusal. FR-030 requires the mode be recorded at all, so
     a disposition that discarded the observation would contradict the
     requirement it enforces and would leave the refusal itself unauditable —
     an absent row and a refused row would be indistinguishable, and neither
     replay nor review could tell a smoke that was never run from one that was
     rejected. The remedy is re-running the smoke on the subscription path;
     the recorded mode MUST NOT be relabeled, which is the same
     re-run-never-relabel disposition FR-031a.7 fixes for an unevidenced
     demonstration.
- **FR-031**: The three smoke runs MUST demonstrate, respectively, a real
  dispatch-time escalation (adaptive), a real inherit resolution (unpinned), and a
  real parallel dispatch with child aggregation (orchestration-changing).
- **FR-031a**: FR-031's word "real" MUST be decidable from recorded evidence
  rather than asserted by the operator, so each demonstration MUST name the
  parameter it sets, the already-frozen observable that proves the parameter
  took effect, and the source that observable is read from. Left unnamed,
  "demonstrates a real escalation" is satisfied by a harness that recorded its
  own intent:
  1. **Read-back rule, all three** — every observable is read from the evidence
     the run produced, never from the dispatch request that asked for it. This
     adopts the rule the frozen CAR-003 treatment runner already applies, under
     which the agent that ran is read from the run transcript rather than from
     the request, and the effective model is read from the per-model consumption
     evidence rather than inferred from configuration. A demonstration evidenced
     only by the request MUST be refused.
  2. **Adaptive — dispatch-time parameter** — the adaptive control MUST declare,
     as a hash-relevant member of its FR-003 execution contract, the documented
     dispatch-time parameter it sets to move between ladder entries, together
     with the platform documentation reference that makes it documented. The
     PRD requires the policy be exercised through the documented dispatch-time
     model parameter, and a control that names no parameter leaves the one thing
     the control does to Implement. An undocumented or inferred parameter MUST
     NOT be declared.
  3. **Adaptive — escalation observable** — an escalation is demonstrated when
     the frozen configured-route proof for the post-escalation attempt records
     the `model`, `effort`, and `candidate_route_id` of the ladder entry at
     index i + 1 while the pre-escalation attempt records index i, both read
     back under rule 1. Matching route identifiers alone are insufficient; the
     served model and effort must move with them.
  4. **Unpinned — inherit observable** — a real inherit resolution is
     demonstrated when the configured-route proof records a `model` and `effort`
     equal to the pinned `parent_session_model` and `parent_session_effort` the
     frozen environment contract carries, read back under rule 1. A declaration
     of inherit in the agent's own configuration is the input, not the
     observable, and MUST NOT stand as the demonstration: the whole point of the
     unpinned arm is what the platform resolved, not what the arm requested.
  5. **Orchestration-changing — parallel observable** — a real parallel dispatch
     is demonstrated when the FR-016d unit holds at least two members besides
     the parent and the parent's own recorded wall time is strictly less than
     the sum of those members' recorded wall times. Under serial dispatch the
     parent's window contains each child end to end, so its wall time is at
     least their sum; strict inequality is therefore only reachable under
     overlap. Both quantities are already-frozen trace members, so no field is
     added. The aggregation half is demonstrated separately by the unit's
     additive dimensions equalling the parent-plus-children sum under FR-016 and
     FR-016e.

     **The premise the rule rests on MUST be declared, not assumed.** The
     containment argument holds only if the parent's recorded wall time is its
     full elapsed window — dispatch to completion, inclusive of time spent
     awaiting its children — and the frozen trace declares that member as a
     bare nullable integer with no such semantics attached. The
     orchestration-changing control's frozen child shape MUST therefore declare,
     as a hash-relevant member alongside the FR-016d dispatch mechanism, that
     every unit member's recorded wall time is its full elapsed window on that
     reading. A topology whose parent wall time excludes child wait is not
     freezable under CAR-004, because the same inequality would then be
     reachable under serial dispatch and the observable would admit a false
     positive. With the declaration the rule is sound but only *sufficient*:
     failing it does not prove serial dispatch, which is why a unit that fails
     it is recorded as not demonstrated under rule 7 rather than as evidence of
     anything.

     **An undecidable comparison is not a demonstration.** The frozen wall-time
     member is nullable. A null on the parent or on any member of the compared
     set leaves the inequality undecidable, and the unit MUST then be recorded
     as not demonstrated under rule 7 — never as satisfied by the members that
     did report, and never with a missing value read as zero, which would make
     the inequality trivially true and invert the whole check. This is the same
     unobserved-rather-than-zero disposition FR-016e fixes for the aggregate
     quantities.
  6. **Precondition on rules 3 and 4** — both turn on the served model being
     decided by the declared parameter or by the parent session, and a
     session-level subagent-model override supersedes both, which is why the
     frozen environment contract carries a `claude_code_subagent_model_unset`
     observation at all. Every smoke MUST therefore record that already-frozen
     observation, so all three carry one record shape, and the observation gates
     rules 3 and 4 specifically: an adaptive or unpinned smoke that cannot record
     it true MUST NOT be reported as demonstrating its behavior, because the
     served model would then be decided by the override rather than by the
     declared parameter or the parent session. This records an existing
     observation on CAR-004's own smoke record; it neither adds a field nor
     builds the preflight and manifest machinery a later spec owns.
  7. **An unevidenced demonstration is not one** — a smoke that completes
     without its observable MUST be recorded as not demonstrated and MUST NOT be
     counted toward FR-031 or SC-009. The remedy is re-running the smoke, never
     relabeling the record. The demonstration state is a CAR-004-owned closed
     member of the smoke record rather than a score-plane failure code, because
     a non-scored smoke row produces no score bundle for such a code to sit on.

  Rules 1, 3, 4, 5, and 7 are FR-034 category 7 decision-semantics entries; the
  declared parameter of rule 2 and rule 5's wall-time-window declaration are
  declared members under categories 2 and 4, and are therefore derived
  mechanically under FR-034a rather than transcribed.
- **FR-032**: Smoke runs MUST preserve cache isolation between arms so that no
  control's smoke warms another arm's cache.
- **FR-032a**: FR-032 MUST name the observable that discharges it and the
  disposition of each way it can fail, or it states an obligation nothing can
  check — the same defect FR-015a was written to remove for the reroute trigger:
  1. **The observable is already frozen** — isolation is evidenced through the
     frozen cache diagnostic's `observed_cache_isolation` object and its four
     members: the three-member `status`, this arm's cache-root digest, the
     paired arm's cache-root digest, and the disjointness flag. No new field,
     status, or code is coined, so FR-009 holds.
  2. **Precommitment is not evidence** — the frozen experiment policy's
     `per_arm_ephemeral_root` assignment constant is a precommitment that arms
     will be isolated, not evidence that they were. A smoke MUST carry the
     observation as well, and the precommitment alone MUST NOT be recorded as
     the isolation claim.
  3. **Three dispositions, all frozen** — `observed_disjoint` is the only status
     under which a smoke stands as FR-031 evidence, and it MUST carry both root
     digests and a true disjointness flag. `observed_shared` is a confirmed
     breach and is recorded with the frozen closed `infrastructure_failure` code
     at `failure_plane=infrastructure`, because a warmed cache distorts the
     measurement of a run rather than the route delivered to it. `unobserved` is
     an evidence-completeness failure recorded with the frozen closed
     `required_evidence_missing` code at `failure_plane=evidence_boundary`.
     Both non-disjoint statuses invalidate the affected smoke as FR-031
     evidence; neither may be treated as a warning.
  4. **The claim is pairwise across the whole series** — the three smokes are
     one ordered series of three arms, so the isolation claim is discharged over
     all three unordered arm pairs, each recorded in the frozen single-pair
     shape, and every pair MUST be `observed_disjoint`. Recording only the
     immediately preceding run would leave the first and last arms unpaired,
     while the acceptance scenario reasons over consecutive runs for different
     controls generally.

     The frozen record is shaped as one arm plus one paired arm, so the pairing
     had to be chosen rather than read off, and the two alternatives are
     rejected on stated grounds so the twin mirrors this choice rather than
     re-deciding it. *Consecutive pairs only* is rejected because FR-032's
     obligation is that no control's smoke warms **another** arm's cache — a
     claim quantified over arms, not over adjacency — so a two-pair record
     leaves exactly the first-to-last pair unchecked, which is a case FR-032
     forbids rather than one it excuses. *A single series-level root-set
     disjointness assertion* is rejected because the frozen object carries one
     arm digest and one paired-arm digest, so a set-level claim could not be
     recorded without coining a new shape, which FR-009 forbids. At three arms
     the all-pairs reading costs three records, so completeness is available
     without any relaxation and there is no reason to buy a weaker claim.
  5. **The unit is inside the arm's root** — for the orchestration-changing
     control the arm's recorded root MUST cover the parent and every FR-016d
     unit member, so a child cannot fall outside the arm's isolation claim. A
     unit member that used a root outside the arm's own makes that arm's status
     other than `observed_disjoint`.
  6. **Roots are digests, never paths** — a cache root MUST be recorded as a
     digest and never as a filesystem path, which is enough to decide
     disjointness without committing an operator-only path. This is the frozen
     record's own rule and it also keeps FR-033's untracked-output discipline
     from being undone by a path leaking into a committed artifact.
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
     row-resolution precedence over the closed signal-source set and the two
     map-consistency rules against the frozen plane derivation and
     candidate-plane pairing, the ordered route sequence that defines
     "next-higher qualified route", the clean-pass streak accounting, the scope
     each retry and cancellation bound is counted over and the terminal state
     each bound breach records, the frozen observable that identifies a
     platform-initiated route change and its effect on the escalation allowance,
     the streak, and an orchestration unit, the membership of the aggregation
     unit, its required agreement with the frozen parent-child graph wherever a
     member's evidence binds one, the parent-plus-children aggregation rule for
     every dimension the frozen Pareto rule reads and for the raw-token vector's
     reasoning member and the two cache-diagnostic quantities the smoke bounds
     constrain, the unobserved-rather-than-zero disposition when one of those is
     unrecorded, the scope each smoke bound is counted over together with the
     elapsed-versus-additive reading of the wall clock and the rule that a child
     dispatch consumes no attempt, the read-back rule and the three
     exact-treatment observables that make an escalation, an inherit resolution,
     and a parallel dispatch demonstrated rather than asserted, the
     constraining reading of the recorded authentication mode, the frozen
     observable that discharges cache isolation with its pairwise scope and its
     three dispositions, the eligibility floors, the material-dominance
     margin test, and the verdict-to-claim-class mapping. This category is
     mandatory
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
  in prose. Both of the smoke half's enforcement points refuse a reserved
  objective: the plan never emits one, and the seal never accepts one.
  [FR-026] [FR-026a]
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
- **SC-012**: Every control, the control-registry document, and the comparison
  contract carry a recorded freeze timestamp and a content address in a committed
  artifact, and an automated check recomputes each digest under the single frozen
  preimage rule and confirms it matches the recorded one.
  [FR-002] [FR-002a] [FR-002b] [FR-002c]
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
- **SC-017**: The registry's three raw-token smoke bounds sum to exactly the
  declared `raw_token_ceiling` member of 1,000,000 as a machine-checked identity,
  every other smoke-bound member carries a frozen value including both cache-write
  TTL classes, and both new contract documents validate with no reference
  resolving outside their own `#/$defs/`. [FR-023] [FR-030] [FR-030a]
- **SC-018**: Every CAR-003 binding recorded by a CAR-004 document has its digest
  recomputed from the bound document's committed bytes, and a seeded byte change
  to any bound document fails that check — so additive-only discipline is
  machine-enforced rather than resting on diff review alone. [FR-005a]
- **SC-019**: The claim-class lookup returns exactly one permitted wording class
  for every outcome the frozen decision procedure can reach, including the
  eligibility-floor no-verdict outcome, and the verdict enum still carries
  exactly three members. [FR-024] [FR-024a]
- **SC-020**: Both partition entries register successfully through the frozen
  registration path with `owning_spec` recorded as `CAR-004`, and a seeded
  duplicate partition identifier or a seeded shared objective identifier fails
  registration closed — so disjointness is proven rather than asserted.
  [FR-025a] [FR-025d] [FR-025b]
- **SC-021**: A seeded membership change to a mirrored CAR-003 enum fails the
  set-equality check on every CAR-004 member bound to it, rather than being
  absorbed silently into an unchanged content address. [FR-010a]
- **SC-022**: Every row the adaptive control can observe resolves to exactly one
  policy response — zero rows resolving to none and zero resolving to two — with
  every source FR-008 admits carrying both a mapped response and a precedence
  rank, and with the plane and terminal-state maps machine-checked against the
  code map under the frozen plane derivation and candidate-plane pairing.
  [FR-010b] [FR-010c]
- **SC-023**: Each declared retry and cancellation bound has its breach path
  exercised by a committed replay fixture that records the frozen terminal state
  and its paired candidate-plane failure code, and the resulting aggregate folds
  to a non-`completed` state with acceptance 0 — so the bounds are proven on the
  breach as well as on the respected path. [FR-014a]
- **SC-024**: The clean-pass streak is proven not to advance on an objective in
  which the policy escalated, neither to advance nor to reset on a non-scorable
  objective, and to reset whenever de-escalation is evaluated at a boundary with
  the streak at three — including at the ladder floor, where no step and no
  wrap-around occur. [FR-012a]
- **SC-025**: The aggregation unit's membership is decidable from the spawning
  link each row records, with nested descendants inside it for both the additive
  sum and the fan-out ceiling; a unit member recording no terminal state fails
  the fold closed rather than being folded over; and a `service_reroute` anywhere
  in the unit makes the whole unit non-scorable. [FR-016d] [FR-015a]
- **SC-026**: Each of the three smokes records its named observable read back
  from run evidence rather than from the dispatch request, and a smoke lacking
  that observable is recorded as not demonstrated and counted toward neither
  FR-031 nor SC-009. [FR-031a]
- **SC-027**: Every smoke record carries the already-frozen no-subagent-override
  observation, and no smoke missing it is reported as demonstrating an
  escalation or an inherit resolution. [FR-031a]
- **SC-028**: The orchestration aggregate sums all four frozen raw-token members
  and both cache-diagnostic quantities across the parent and every unit member,
  keyed identically to the ceilings that bound them, with neither cache quantity
  entering the Pareto dimension set or the raw-token identity, and an unrecorded
  quantity reported unobserved rather than zero. [FR-016e]
- **SC-029**: All four smoke bounds are evaluated over the whole unit, the wall
  clock as elapsed time rather than as the additive duration, with no child
  dispatch consuming an objective attempt. [FR-030b]
- **SC-030**: Every accepted smoke records an observed authentication mode of
  `subscription` through the identified frozen member, and a run observed as
  `api_key` is refused rather than recorded and kept. [FR-030c]
- **SC-031**: All three unordered smoke-arm pairs record `observed_disjoint`
  with both root digests present and no root recorded as a filesystem path; a
  seeded shared or unobserved pair invalidates the affected smoke under its
  frozen code and plane. [FR-032a]

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
- **"Clean pass" is defined by FR-012a.1**, against already-frozen terminal state
  and failure classification rather than a new notion of success: terminal state
  `completed`, failure code `none`, zero retries, and no declared budget trigger
  met. The bar is the declared trigger rather than a budget breach, and it is
  narrower than the frozen `accepted` score disposition, which also covers
  candidate terminal outcomes carrying acceptance 0.
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
  `max_output_tokens: 50000`. The ceiling itself is a declared member,
  `raw_token_ceiling: 1000000`, and the three raw-token bounds sum to exactly
  that member, asserted as an identity so FR-030's ceiling is machine-checked
  rather than prose and so FR-034 category 6 derives it from the committed bytes
  instead of transcribing it (FR-030a).
  `max_cache_write_tokens_by_ttl_class` is declared over the frozen
  `ephemeral_5m` and `ephemeral_1h` classes at `ephemeral_5m: 160000` and
  `ephemeral_1h: 40000`. Cache write scales with dispatches rather than with
  input, and the repository's two instances settle which basis to use. They agree
  exactly on the `ephemeral_5m` allowance per attempt — the frozen CAR-003
  campaign budget pairs 48 attempts with 800,000 and the calibration-pilot
  envelope pairs 24 attempts with 400,000, both 16,666.7 tokens per attempt —
  while their input-relative proportions differ by a factor of twenty, 20% of a
  4,000,000 input ceiling against 400% of a 100,000 one. Attempts are therefore
  the only basis the repository's own evidence supports, and any input-anchored
  derivation is refuted outright by the pilot envelope, which declares cache-write
  ceilings well above its input ceiling. Cache write is explicitly *not* bounded
  by `max_input_tokens`.
  The anchor is the frozen campaign budget rather than the operator envelope,
  a frozen instance outranking an envelope: its per-attempt allowance carried over
  the smoke's five attempts is 83,333 for `ephemeral_5m` and 20,833 for
  `ephemeral_1h`. The two declared ceilings sit just under twice that, rounded
  down to a round figure — headroom so a legitimate smoke never trips a diagnostic
  guard, rounded down so the guard stays tighter than the doubling rather than
  looser — and they preserve the frozen budget's own 4:1 ratio between the two
  classes. Both classes stay outside
  the raw-token identity, cache write being diagnostic-only and never a Pareto
  dimension, and the validator enforces that both are present at their frozen
  values and that neither enters that identity; it MUST NOT constrain either class
  against `max_input_tokens`, which is not the governing quantity. Leaving the
  member valueless would place an implementation-chosen number inside a
  hash-relevant object.
  These two ceilings carry the same moderate confidence as the 1,000,000 and
  30-minute caps. The smoke MUST NOT be
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
