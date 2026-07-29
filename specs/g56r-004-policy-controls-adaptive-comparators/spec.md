# Feature Specification: G56R-004 Policy Controls and Adaptive Comparators

**Feature Branch**: `g56r-004-policy-controls-adaptive-comparators`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "Freeze Codex-local policy controls and adaptive
comparators before G56R-011 observes final static-core outcomes. Mirror
CAR-004's complete cross-platform semantics against the frozen G56R-003/CAR-003
evaluation surface while preserving the one sanctioned platform divergence:
Codex freezes unpinned, adaptive, and justified-high-effort controls."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Freeze the policy controls before final routing outcomes exist (Priority: P1)

[US1] The Codex routing evaluation program needs the later G56R-011 release
comparison to be reproducible and predeclared. Before the final static
`core_routing_policy_id` exists, G56R-004 freezes the three exact-treatment
policy controls, the adaptive response contract, the resource and quality floors,
the statistical dominance rule, the untouched G56R-011 comparison partition, and
the release wording consequence. The feature records those decisions as
content-addressed, Codex-local contracts that mirror CAR-004 against frozen
G56R-003/CAR-003 evidence. G56R-004 does not decide which policy wins.

**Why this priority**: This is the whole feature and one independently testable
vertical slice. G56R-011 cannot make a trustworthy final dominance decision if
the controls, margins, partitions, and claim restrictions are chosen after the
static routing core reports outcomes. G56R-005/G56R-006 also inherit the bounded
control and route-eligibility semantics from this frozen surface.

**Independent Test**: Fully testable without any later routing policy. The
repository checks can validate that exactly three Codex controls are frozen, the
Codex contracts mirror the CAR-004 handoff except for the sanctioned third
control value, frozen G56R-003/CAR-003 bindings verify by stable ID and digest,
adaptive rows resolve exactly once, replay is deterministic, reserved objectives
are refused, and every reachable verdict maps to one release claim class. The
three live smokes are bounded, non-scored, operator-authorized checks on the
supported ChatGPT sign-in path and do not produce qualification evidence.

**Acceptance Scenarios**:

1. **Given** the Codex policy-control registry, **When** controls are enumerated,
   **Then** exactly three are present - unpinned, adaptive, and
   justified-high-effort - and a fourth control or topology-changing control arm
   is rejected. [FR-001]
2. **Given** the CAR-004 twin handoff, **When** the G56R-004 mirror surface is
   derived in both directions, **Then** every mirror-required shape, member,
   enum, numeric, decision semantic, and guard is present; **And** the only
   sanctioned divergence is the third control-kind enum value. [FR-002] [FR-006]
3. **Given** the frozen G56R-003/CAR-003 evaluation contracts, **When** a
   G56R-004 document records a binding, **Then** the binding uses a stable ID and
   committed-bytes digest, and any digest mismatch fails closed without editing
   the frozen artifact. [FR-004] [FR-005]
4. **Given** a frozen control or comparison document, **When** any hash-relevant
   field or freeze timestamp changes, **Then** the content address changes and
   the result is a new version rather than an in-place mutation. [FR-003]
5. **Given** the frozen parent Codex session context, **When** the unpinned
   control is resolved, **Then** it inherits the bound parent model, effort,
   client, and environment; **And** a different parent context produces a
   different control identity. [FR-008] [FR-009]
6. **Given** the adaptive control's route ladder, **When** a route is selected
   or changed, **Then** every reachable route is an ordered admitted G56R-003
   tuple, no unqualified route is discovered at runtime, and floor/ceiling
   movement never wraps. [FR-010] [FR-011] [FR-014] [FR-017]
7. **Given** an adaptive evidence row carrying terminal, failure, retry, and
   budget signals, **When** the row is resolved, **Then** exactly one response is
   produced under the declared precedence and consistency rules. [FR-012]
   [FR-013]
8. **Given** a platform-initiated service reroute, **When** the adaptive state is
   updated, **Then** the row is non-scorable, consumes no escalation allowance,
   moves no ladder position, and neither advances nor resets the clean-pass
   streak. [FR-016]
9. **Given** the justified-high-effort control, **When** its binding is
   validated, **Then** it references one already-qualified high-effort route,
   carries an eligibility predicate and rationale, and refuses any unqualified or
   dynamically discovered route. [FR-018] [FR-019]
10. **Given** automatically spawned child work under a control, **When** evidence
    is aggregated, **Then** parent and child cost, terminal-state, acceptance,
    retry, compaction, raw-token, and cache quantities are included under the
    mirrored parent-plus-children semantics rather than treated as a fourth
    control arm. [FR-020] [FR-021] [FR-022]
11. **Given** an ineligible control, **When** the comparison contract is applied,
    **Then** no dominance verdict is reached and the claim-class lookup still
    returns the no-comparative-claim result. [FR-024] [FR-028] [FR-029]
12. **Given** eligible static and control evidence, **When** dominance is
    evaluated, **Then** the comparison runs gate-first, uses the eight
    direction-aware dimensions, applies the 10% relative margins only where
    allowed, handles zero denominators exactly, and introduces no weighted score.
    [FR-025] [FR-026] [FR-027] [FR-028]
13. **Given** a dominant control outcome in G56R-011, **When** release language is
    generated, **Then** static defaults may still ship for declared operational
    simplicity but must not claim efficient, optimal, or best-measured routing.
    [FR-029] [FR-030]
14. **Given** the reserved G56R-011 integrated-confirmation partition, **When** a
    replay or smoke row attempts to consume one of its objectives, **Then** the
    guard fails at the replay path and at smoke plan/seal time. [FR-031] [FR-032]
15. **Given** deterministic replay fixtures for all three controls, **When** they
    are replayed twice, **Then** they produce byte-identical governed results and
    no outcome-bearing scored evidence. [FR-034]
16. **Given** operator authorization for live smoke, **When** one ChatGPT sign-in
    smoke runs for each control, **Then** every smoke is non-scored, stays inside
    the frozen objective, repetition, token, time, component, and cache ceilings,
    records exact-treatment evidence read back from execution, and keeps raw
    captures off-repository. [FR-035] [FR-036] [FR-037] [FR-038] [FR-039]
17. **Given** a mirror-required CAR-004 member that Codex cannot represent,
    **When** the completeness check names it, **Then** G56R-004 does not weaken or
    silently omit the member; it records the declined member and raises the
    paired roadmap reconciliation disposition. [FR-041]
18. **Given** a PR review packet for this feature, **When** reviewers inspect it,
    **Then** it maps requirements and success criteria to changed files,
    evidence, non-goals, known gaps, rollback or non-applicability notes, and
    the reviewability budget. [FR-042]

### Edge Cases

- **Second divergence detected**: any difference besides the third control-kind
  enum value fails the mirror check, even if the local Codex fixture still
  validates. [FR-006]
- **Digest drift in frozen evidence**: a G56R-003 or CAR-003 binding whose
  committed bytes no longer match the recorded digest fails closed and cannot be
  repaired by editing the frozen artifact. [FR-004] [FR-005]
- **Adaptive ladder ceiling or floor**: an escalation at the final ladder entry,
  or a de-escalation at the first entry, records no step and never wraps to the
  other end. [FR-014]
- **Non-scorable row inside a clean-pass streak**: a non-scorable objective is
  excluded from the streak rather than counted clean or used to reset the
  counter. [FR-014] [FR-016]
- **Zero denominator**: a margin-eligible component whose comparator value is
  zero records `margin_not_computable` and cannot supply material dominance.
  [FR-028]
- **Null acceptance or missing terminal state**: null acceptance makes comparison
  uncertain unless the terminal-state floor forces zero; a missing terminal
  state makes the aggregate malformed and fails closed. [FR-021]
- **Unobserved cache diagnostic**: absent cache evidence is recorded unobserved,
  never coerced to zero. [FR-022] [FR-038]
- **Smoke authorization withheld**: deterministic replay remains the automated
  gate, and any live-smoke success criterion depending on operator execution is
  reported as unrun rather than fabricated. [FR-035]

## Requirements *(mandatory)*

### Functional Requirements

#### Control Set, Identity, and Mirror Boundary

- **FR-001**: The frozen Codex control set MUST contain exactly three controls:
  `unpinned`, `adaptive`, and `justified_high_effort`. Automatically spawned
  child work is a cost and evidence modifier inside a control, not a fourth arm.
  A topology-changing control arm, a fourth control, or duplicate
  `control_kind` value MUST be rejected.
- **FR-002**: G56R-004 MUST author new additive Codex-local control-registry and
  control-comparison contracts with Codex-owned identifiers. Those contracts
  MUST mirror CAR-004's complete record shapes, required-member sets, closed
  enums, frozen numerics, decision semantics, and enforcement guards, except for
  the one sanctioned platform-value divergence in FR-001.
- **FR-003**: Every control, the control-registry document, and the comparison
  document MUST carry a content address computed over the complete frozen
  definition by one canonical preimage rule: SHA-256 over canonical JSON with
  sorted keys, minimal separators, UTF-8, no NaN, declared array order preserved,
  and the record's own digest member removed. The `frozen_at` timestamp MUST be
  inside that preimage as a `Z`-suffixed UTC instant.
- **FR-004**: Every binding to frozen G56R-003 or CAR-003 evidence MUST record
  the bound artifact's stable ID and committed-bytes SHA-256 digest. Automated
  validation MUST recompute each digest from the committed bytes and fail closed
  on mismatch.
- **FR-005**: G56R-004 MUST NOT edit, re-version, weaken, or remove any frozen
  G56R-003 or CAR-003 contract, fixture, trace, score bundle, partition, or
  evidence record. Existing CAR-012/G56R-012 reconciliation debt remains outside
  this feature.
- **FR-006**: Mirror completeness MUST be checked bidirectionally. A delivered
  member absent from the mirror record, a recorded member absent from Codex
  artifacts, an invented member, an enum or numeric drift, a digest mismatch, a
  missing mirror obligation, or more than one mirror obligation on an entry MUST
  fail closed. The only sanctioned divergence is the third control value named
  in FR-001.
- **FR-007**: Nulls, zeros, units, comparison directions, closed enum members,
  and frozen numeric values inherited from CAR-004 or the frozen G56R-003/CAR-003
  surface MUST be preserved exactly. No validation path may normalize missing
  evidence to zero or reinterpret an unordered categorical field as ordered.

#### Unpinned Control

- **FR-008**: The unpinned control MUST freeze exactly one arm bound to the
  frozen parent-session context: model, effort, client version, authentication
  mode, and environment boundary. A changed parent context produces a new
  content-addressed control version rather than a second concurrent arm.
- **FR-009**: Exact treatment for the unpinned control MUST be demonstrated from
  execution evidence, not dispatch intent: the served model and effort must equal
  the pinned parent context and all local model, effort, provider, service-tier,
  and API-key overrides required to be absent by the frozen environment contract
  must be observed absent.

#### Adaptive Control

- **FR-010**: The adaptive ladder MUST derive only from ordered, admitted
  G56R-003 successor-capability tuples. Every ladder entry MUST resolve to one
  admitted `candidate_route_id`; no unqualified route, hidden route, or
  dynamically discovered route may be selected after the control is frozen.
- **FR-011**: Ladder order MUST be hash-relevant and declared. Within one model,
  route order MUST agree with the frozen Codex ordinary-effort ladder
  `low -> medium -> high -> xhigh -> max`. Cross-model steps MUST carry a
  non-empty rationale because model identifiers themselves are unordered.
- **FR-012**: Adaptive signals MUST bind exclusively to frozen observed members:
  terminal state, failure plane, failure code, retry count, and raw-token or
  duration budget thresholds. G56R-004 MUST NOT add telemetry fields or infer
  signals from prose, timestamps, route names, or dispatch intent.
- **FR-013**: The adaptive signal-to-response mapping MUST be total and
  single-valued over the closed response set `escalate`, `hold`, and
  `non_scorable`. Row resolution MUST use the frozen precedence
  `failure_code > failure_plane > retry_count > budget_threshold >
  terminal_state`. The failure-plane map MUST agree with the failure-code map
  under the frozen plane derivation, and terminal-state responses MUST agree
  with the paired candidate-plane failure codes.
- **FR-014**: The adaptive control MUST permit at most one escalation per
  objective, only to the next higher ladder entry. De-escalation MUST be decided
  only between objectives after exactly three consecutive clean passes, never
  mid-objective, and never by wrapping at the ladder floor or ceiling. A clean
  pass is `completed`, failure code `none`, zero retries, and no declared budget
  trigger met; an escalating objective is never clean; a non-scorable objective
  neither advances nor resets the streak.
- **FR-015**: Retry and cancellation bounds MUST declare their scope and breach
  outcome. Escalation MUST NOT reset either bound. A retry-bound breach records
  the frozen failed/candidate-failed pairing; a cancellation-bound breach records
  the frozen cancelled/candidate-cancelled pairing. Replay MUST exercise both
  respected and breached paths.
- **FR-016**: A platform-initiated route change MUST be identified by the frozen
  `service_reroute` failure code. It resolves to `non_scorable`, consumes no
  escalation allowance, changes no ladder position, neither advances nor resets
  the clean-pass streak, and makes the whole parent-plus-children unit
  non-scorable when present anywhere inside that unit.
- **FR-017**: An adaptive control version MUST become invalid rather than
  self-repair when the bound successor-capability freeze changes, an admitted
  tuple disappears, a new admitted tuple is present but absent from the ladder,
  or the frozen effort-order evidence no longer supports the declared order.

#### Justified-High-Effort Control

- **FR-018**: The justified-high-effort control MUST bind one already-qualified
  high-effort route from frozen G56R-003 evidence. The binding MUST record the
  route ID, model, effort, successor-freeze ID, freeze digest, route-evidence
  digest, and the reason the route is eligible before any G56R-011 outcomes
  exist.
- **FR-019**: The justified-high-effort control MUST carry an explicit
  eligibility predicate and human-readable rationale. If the predicate is false,
  missing, or not reproducible from frozen evidence, the control is ineligible
  and no dominance verdict may be produced for it.
- **FR-020**: Any automatically spawned child work under the
  justified-high-effort control MUST be included in the governed evidence as part
  of the same parent-plus-children unit. The control MUST NOT discard spawned
  work, report parent-only cost, or register child work as a separate policy arm.
- **FR-021**: Parent-plus-children aggregation MUST be defined for every
  decision-bearing dimension. Input tokens, cached input tokens, output tokens,
  duration, retries, and compactions sum across the parent and every child. The
  aggregate terminal state is worst-wins over the frozen terminal-state severity
  order. Aggregate acceptance is the parent objective's acceptance-oracle result,
  floored to zero whenever the aggregate terminal state is not `completed`; null
  acceptance is allowed only as a reported evidence gap on an otherwise
  completed unit.
- **FR-022**: Raw-token and cache aggregation MUST preserve the mirrored member
  sets. The raw-token vector sums input, cached input, output, and reasoning
  output tokens; reasoning output tokens are reported but never enter dominance
  or the raw-token ceiling. Cache read and cache write by TTL class aggregate
  additively, are checked only against their own ceilings, and remain
  diagnostic-only.
- **FR-023**: Exact treatment for the justified-high-effort control MUST be read
  back from produced evidence: the served model, effort, route ID, eligibility
  predicate result, rationale binding, and parent-plus-child aggregate must match
  the frozen control definition. A smoke lacking those observables is recorded as
  not demonstrated, never relabeled as success.

#### Comparison Contract

- **FR-024**: A control MUST become eligible for a dominance verdict only after
  every mandatory contract, safety, role, quality, reliability, and availability
  gate passes. An unmet floor returns the frozen no-verdict outcome and the
  no-comparative-claim class rather than `not_dominant`.
- **FR-025**: Dominance MUST be decided in the frozen gate-first order:
  eligibility floors, environment-independent Pareto comparison, then
  materiality margin. No price coefficient, weight, scalar score, or forced rank
  may be introduced.
- **FR-026**: The comparison MUST use exactly eight direction-aware dimensions:
  `input_tokens`, `cached_input_tokens`, `output_tokens`, and `duration` are
  lower-is-better and margin-eligible; `retries` and `compactions` are
  lower-is-better and no-worse-only; `acceptance` is higher-is-better and
  no-worse-only; `terminal_state` is categorical equal-only and no-worse-only.
  The resource-vector `duration_ms` member MUST project to the decision dimension
  `duration`.
- **FR-027**: Material dominance MUST require at least one margin-eligible
  dimension to clear a 10% relative improvement while no dimension is worse. A
  margin clears only when the frozen one-sided lower confidence bound on relative
  improvement is at least 0.10. Deterministic replay fixtures may use the point
  estimate only as the declared non-outcome-bearing stand-in.
- **FR-028**: A zero comparator denominator MUST produce
  `margin_not_computable`, never an infinite, undefined, or 100% improvement.
  Mixed, tied, incomplete, statistically uncertain, null-acceptance, or differing
  terminal-state comparisons MUST produce `inconclusive` or no verdict exactly as
  the mirrored rule declares.
- **FR-029**: The comparison contract MUST carry a machine-readable
  verdict-to-claim-class mapping total over `dominant`, `not_dominant`,
  `inconclusive`, and the eligibility-floor no-verdict outcome. Only `dominant`
  carries a messaging restriction.
- **FR-030**: A materially dominated static policy MAY still ship for declared
  operational simplicity, but release wording MUST NOT call it efficient,
  optimal, or best-measured. G56R-004 itself MUST NOT issue a final dominance
  conclusion about the future static core.

#### Reserved Comparison Partition

- **FR-031**: G56R-004 MUST create a content-addressed reserved partition entry
  for G56R-011 integrated confirmation and a separate non-qualification smoke
  partition for G56R-004. The reserved entry MUST bind its partition ID,
  objective IDs, sorted objective-set digest, partition type, qualification
  eligibility, owner, and freeze timestamp.
- **FR-032**: One guard MUST reject any replay row or smoke row consuming a
  reserved G56R-011 objective. The replay half runs in committed deterministic
  checks; the smoke half must be enforced before an operator receives a plan and
  again when any smoke record is sealed.
- **FR-033**: G56R-004 evidence MUST consume zero G56R-011 integrated
  confirmation objectives, zero selection or cohort-lock objectives, and zero
  outcome-bearing scored objectives. Smoke objectives MUST come only from the
  non-reserved G56R-004 smoke partition and remain non-scored.

#### Validation and Evidence Boundary

- **FR-034**: Every control MUST have deterministic replay fixtures, including
  positive and seeded-negative cases, that replay byte-identically across
  repeated runs and prove the relevant exact-treatment, aggregation, guard, and
  comparison behavior without live model execution.
- **FR-035**: Each control MUST have exactly one bounded live smoke requirement
  on the supported ChatGPT sign-in path. Live smoke execution requires explicit
  operator authorization, must not run in default CI, and cannot be replaced by
  API-key smoke. If authorization is absent, the affected smoke evidence and
  success criteria remain honestly unrun.
- **FR-036**: Smoke bounds MUST mirror CAR-004: at most five non-reserved
  objectives, one repetition, zero reserved confirmation entries, 1,000,000 raw
  tokens, and 30 minutes elapsed wall clock per control. The component ceilings
  are 800,000 input tokens, 150,000 cached input tokens, 50,000 output tokens,
  1,200,000 cache-read tokens, 160,000 five-minute cache-write tokens, and
  40,000 one-hour cache-write tokens. Every bound MUST declare unit, direction,
  and parent-plus-children scope.
- **FR-037**: Smoke records MUST be non-scored and must read exact-treatment
  observables from produced evidence, never from dispatch requests. The unpinned
  smoke proves parent inheritance, the adaptive smoke proves served model,
  effort, and route movement from ladder index `i` to `i + 1`, and the
  justified-high-effort smoke proves the frozen eligible high-effort route and
  governed parent-plus-child aggregation.
- **FR-038**: Smoke cache isolation MUST be proven for all three unordered
  control pairs. `observed_disjoint` with both root digests present is the only
  accepted status; shared or unobserved cache roots invalidate the affected
  smoke under the frozen failure-plane/code mapping. Root evidence is recorded
  as digests, never filesystem paths.
- **FR-039**: Raw live model, prompt, response, local path, and operator capture
  material MUST remain off-repository. Committed evidence may include only
  governed summaries, digests, refusal records, and replay fixtures that reveal
  no raw captured conversation content.

#### Twin Handoff and Reconciliation

- **FR-040**: G56R-004 MUST treat the CAR-004 twin handoff as the complete mirror
  authority applied to the frozen G56R-003/CAR-003 surface. Codex-owned IDs,
  paths, and route tuples replace CAR-owned literals, but mirror-required
  semantics and guards remain intact.
- **FR-041**: If implementation finds a mirror-required member Codex genuinely
  cannot represent, G56R-004 MUST name that member, keep the CAR-004 obligation
  unweakened, record the declined disposition, and raise the paired CAR/G56R
  roadmap reconciliation item. Silent omission, best-effort weakening, or
  editing CAR-004/G56R-003/CAR-003 artifacts is forbidden.
- **FR-042**: The PR review packet MUST include what changed, why, non-goals,
  review order, scope budget, traceability, verification evidence, known gaps,
  operator-only smoke status, rollback or non-applicability notes, and an
  explicit statement that no production routing, installer, manifest, scheduler,
  default, or release integration behavior changed.

### Reviewability Notes

- Setup and roadmap evidence keep G56R-004 as one thin vertical slice. The
  feature's primary surface is repository-only harness/adapter validation. It
  changes no install-facing plugin runtime, manifest, payload, scheduler, or
  shipped default behavior.
- The design concept records `estimated_loc: 235`, `suggested_slices: 1`, and
  `status: ok`. The plan phase must re-check the concrete file plan and split
  only if the authoritative reviewability gate later requires it.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: schema/fixture and docs/process evidence
- **Projected reviewable LOC**: 235
- **Projected production files**: approximately 3
- **Projected total files**: approximately 10
- **Budget result**: within budget for one reviewable slice
- **Split decision**: Keep one spec because the feature is one P1
  precommitment slice; do not split unless Plan's concrete reviewability gate
  expands past the one-slice threshold.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, operator-only
  smoke status, and rollback or non-applicability notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue, including any
  reconciliation raised under FR-041.

### Key Entities

- **Policy Control**: One frozen, content-addressed Codex policy-level
  alternative to the future static core. Exactly three exist in this feature.
- **Unpinned Control**: The single control that inherits the frozen parent
  session's model and effort.
- **Adaptive Control**: The frozen ladder and response rule that escalates or
  de-escalates only among admitted G56R-003 route tuples.
- **Justified-High-Effort Control**: The single already-qualified high-effort
  route plus eligibility predicate, rationale, and parent-plus-child cost
  evidence.
- **Control Identity**: The content address over a control's complete frozen
  definition, including `frozen_at`.
- **Control Registry**: The Codex-local document that freezes the closed
  control set, shared bounds, G56R-003/CAR-003 bindings, and registry digest.
- **Control Comparison Contract**: The Codex-local document that freezes
  eligibility floors, Pareto and materiality semantics, confidence, multiplicity,
  reserved-partition binding, and claim-class mapping.
- **Reserved Comparison Partition**: The content-addressed G56R-011 objective
  set registered now and protected from replay or smoke consumption.
- **Replay Fixture**: Deterministic non-live evidence used to prove contract
  behavior and negative controls.
- **Smoke Record**: One non-scored, operator-authorized ChatGPT sign-in run per
  control, sealed only as governed evidence and never as qualification evidence.
- **Twin Completeness Record**: The machine-checkable comparison between the
  CAR-004 handoff and the Codex-local mirror surface.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The control registry contains exactly three controls with unique
  control kinds: `unpinned`, `adaptive`, and `justified_high_effort`; seeded
  fourth-control and duplicate-kind registries fail automatically. [FR-001]
- **SC-002**: Every control, the registry document, and the comparison document
  recomputes to its recorded content address; seeded changes to any
  hash-relevant field or `frozen_at` timestamp produce a different digest.
  [FR-003]
- **SC-003**: 100% of recorded frozen G56R-003/CAR-003 bindings verify by stable
  ID and committed-bytes digest; a seeded byte change to each bound document
  fails closed. [FR-004] [FR-005]
- **SC-004**: The bidirectional mirror check reports zero missing, extra,
  drifted, digest-mismatched, or obligation-mismatched members, and exactly one
  sanctioned platform divergence. [FR-002] [FR-006] [FR-040]
- **SC-005**: The adaptive ladder contains only admitted G56R-003 tuples, covers
  every required route exactly as declared, preserves within-model effort order,
  records every cross-model rationale, and rejects duplicate, omitted, or
  unqualified entries. [FR-010] [FR-011]
- **SC-006**: 100% of adaptive observable signal values map to exactly one
  response, with precedence, plane/code consistency, terminal/code consistency,
  and budget/retry ranks exercised by deterministic replay. [FR-012] [FR-013]
- **SC-007**: Replay proves one-escalation-per-objective, no wrap at ladder
  floor or ceiling, three-clean-pass de-escalation, non-scorable exclusion, and
  retry/cancellation breach outcomes. [FR-014] [FR-015] [FR-016]
- **SC-008**: The justified-high-effort control binds exactly one qualified
  high-effort route and rejects a missing, unqualified, dynamically discovered,
  or predicate-failing route. [FR-018] [FR-019]
- **SC-009**: Parent-plus-children aggregation is defined for all eight
  decision-bearing dimensions, all raw-token members, and every declared cache
  diagnostic; missing terminal state and unobserved cache cases resolve exactly
  as specified. [FR-020] [FR-021] [FR-022]
- **SC-010**: The comparison contract declares the eight dimensions, directions,
  10% material margins, confidence method, multiplicity position, zero-denominator
  outcome, no-weights rule, and no-verdict mapping exactly once. [FR-024] [FR-025]
  [FR-026] [FR-027] [FR-028]
- **SC-011**: Every reachable comparison outcome returns exactly one permitted
  claim class; only a dominant outcome forbids efficient, optimal, and
  best-measured claims while leaving static shipment allowed for declared
  simplicity. [FR-029] [FR-030]
- **SC-012**: The reserved G56R-011 partition and G56R-004 smoke partition are
  content-addressed, mutually disjoint, registered through the frozen partition
  machinery, and protected by seeded replay and smoke-plan/seal refusal cases.
  [FR-031] [FR-032] [FR-033]
- **SC-013**: Replaying every control fixture twice yields byte-identical
  governed evidence and zero outcome-bearing scored rows. [FR-034]
- **SC-014**: Each authorized live smoke, when run, stays within 5 non-reserved
  objectives, 1 repetition, 1,000,000 raw tokens, 30 minutes elapsed wall clock,
  and all component/cache ceilings; any unrun smoke is reported as unrun rather
  than passed. [FR-035] [FR-036]
- **SC-015**: Smoke records prove exact treatment from produced evidence for
  unpinned inheritance, adaptive escalation, and justified-high-effort
  eligibility/aggregation; request-only proof is rejected. [FR-037]
- **SC-016**: All three unordered smoke-control pairs record cache isolation as
  `observed_disjoint` with digest roots; shared, unobserved, path-based, or
  missing-root evidence invalidates the affected smoke. [FR-038]
- **SC-017**: The repository contains zero raw live model, prompt, response,
  operator-local path, or unsanitized capture material from smoke execution.
  [FR-039]
- **SC-018**: Any unmirrorable CAR-004 member is named with a paired
  reconciliation disposition; there are zero silent omissions, weakened members,
  or frozen-contract edits. [FR-041]
- **SC-019**: The PR packet maps every major FR and SC to changed files and
  verification evidence, records operator-only smoke status, and states that no
  production routing, installer, manifest, scheduler, default, or release
  integration behavior changed. [FR-042]

## Out of Scope

- Editing frozen G56R-003, CAR-003, or CAR-004 contracts, fixtures, evidence,
  partition records, or historical archive material.
- Existing CAR-012/G56R-012 mirrored evaluation-contract reconciliation debt.
- A fourth control, a full topology-changing Codex control arm, or dynamic
  discovery of unqualified routes.
- Production adaptive routing, resolver fallback behavior, installer behavior,
  plugin manifests, scheduler defaults, shipped payloads, or release integration.
- API-key-required smoke execution, committed raw model/prompt/response captures,
  scored mini-campaigns, outcome-bearing control campaigns, or a final dominance
  verdict.
- New telemetry fields, new package/runtime dependencies, active Bash or `jq`,
  and filenames coupled to temporary spec IDs.

## Assumptions

- `docs/ai/specs/.process/G56R-004-design-concept.md` is the scoping authority
  for accepted decisions, including the one sanctioned control-value divergence
  and the exclusion of existing G56R-012 work.
- `docs/ai/specs/.process/CAR-004-twin-handoff.md` is the complete mirror input,
  including categories 7 and 8; G56R-004 mirrors it against Codex-owned IDs and
  frozen G56R-003/CAR-003 bindings.
- G56R-003 is complete and archived from PR #386; its current runtime and
  specification contract evidence lives under
  `tests/speckit-pro/layer6-efficiency/` and
  `docs/ai/research/codex-g56r-003-effort-ladder.json`.
- CAR-004 is treated as landed and available on the current base. Its finished
  spec bundle under `specs/car-004-policy-controls-comparators/` is reference
  evidence, not a file set G56R-004 may mutate.
- Exact Codex IDs and the one justified-high-effort route binding are resolved
  in Clarify/Plan from frozen evidence. This spec freezes the validity rule and
  failure behavior rather than guessing a route literal.
