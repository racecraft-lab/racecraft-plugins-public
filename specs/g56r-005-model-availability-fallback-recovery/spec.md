# Feature Specification: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Feature Branch**: `g56r-005-model-availability-fallback-recovery`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "G56R-005 Model Availability, Fallback, and Recovery Simulation"

## Clarifications

### Session 2026-08-22 — Resolution Contract

- **Q: What exact ordering contract governs diagnostics?** **A:** Evaluate a
  strict override before the route walk. If it is compatible or absent, visit
  the preferred route and then declared fallbacks in order. For each reached
  route, emit every applicable reason in this order: model absence, unsupported
  effort, capability-discovery unavailability, availability-probe failure,
  treatment-probe failure, and non-route treatment mutation. Detect a loop when
  a previously attempted route is reached. Emit exactly one terminal outcome
  last.
- **Q: Is fallback exhaustion a second terminal outcome?** **A:** No. Record
  fallback exhaustion as diagnostic evidence or terminal details and use
  `no_safe_route` as the sole terminal outcome for an exhausted route walk.
- **Q: When is a fallback loop detected?** **A:** Detect it on arrival at a
  route already attempted during the sequential walk; do not re-attempt or
  re-consult that route. Do not reject an unreachable duplicate during a
  pre-walk scan.
- **Q: What proves a validated no-helper continuation?** **A:** The fixture must
  explicitly declare and independently qualify the no-helper continuation,
  prove zero helper-route attempts with counters separate from required-route
  counters, and still prove required-agent success or atomic failure.
- **Q: How is treatment immutability proved?** **A:** Canonically compare and
  digest every non-route treatment field—agent identity, instructions, tools,
  skills and MCP bindings, sandbox, mutation policy, and output contract—and
  permit only model and effort to differ.

### Session 2026-08-22 — State and Recovery

- **Q: What identifies fake-home pre-state and previous-known-good state?**
  **A:** Derive each state ID from a canonical manifest containing sorted
  fake-home-relative paths, SHA-256 content digests, file modes, and
  required/optional role classification. Exclude absolute temporary roots,
  mtimes, inodes, timestamps, and host-specific paths.
- **Q: What is the fake-home adapter's allowed write boundary?** **A:** Require
  an explicit harness-created temporary `fake_home_root` and resolve the only
  writable destination as `<fake_home_root>/.codex/agents`. Checked-in fixture
  roots may seed a copied pre-state but are never mutation targets. Reject real
  homes, path traversal, symlink traversal, and every destination outside the
  resolved boundary.
- **Q: Which failures prove atomic no-write and which trigger rollback?**
  **A:** A failure before any managed file is touched proves atomic no-write and
  does not run rollback. Any later failure, post-copy verification failure, or
  cancellation after a managed file is touched triggers rollback followed by
  best-effort cleanup. Successful rollback restores the exact pre-state and
  reports `writes_state=false`; failed rollback reports `writes_state=true` and
  deterministic manual-remediation evidence. Cleanup never replaces the
  rollback or terminal result.
- **Q: What exact cleanup and replay evidence is required?** **A:** Emit a closed
  canonical JSON Recovery Record with sorted keys and deterministic arrays for
  pre-state and final-state IDs, staged, applied, rolled-back, and cleanup
  actions, sorted cleanup errors, rollback outcome, write-state disposition,
  and manual remediation. Exclude absolute temporary paths and host-specific
  timestamps or metadata.

### Session 2026-08-22 — Bounds and Attribution

- **Q: How are service reroutes separated from plugin route reasons?** **A:**
  Store service reroute evidence in a distinct attribution record with
  `origin=service`, approved/unapproved disposition, observed target route, and
  scoring effect. Do not interleave service attribution with the plugin reason
  sequence; plugin reasons still follow the Resolution Ordering Contract.
- **Q: What makes service reroute evidence approved?** **A:** The observed
  service target must match a declared route or declared allowed route mutation,
  change only model and effort, preserve the non-route treatment digest, and be
  explicitly marked approved by fixture evidence. Otherwise it is unapproved
  service evidence and cannot produce a successful scoring-eligible terminal
  outcome.
- **Q: What is the precedence among budget, cancellation, strict override, and
  route outcomes?** **A:** Incompatible strict override is checked first and
  remains terminal before fallback evaluation or writes. During a normal replay,
  cancellation or any declared budget breach observed before route success is
  terminal for the harness run. After fake-home mutation starts, cancellation
  triggers only the bounded recovery needed to preserve or report state before
  emitting the terminal outcome.
- **Q: How are time, retry, fan-out, context, and escalation bounds represented?**
  **A:** Fixtures declare numeric or closed-enum limits for each bound. The
  harness records consumed counters and terminal breach reason using
  deterministic counters, not wall-clock host metadata. Fan-out greater than
  one, recursive agent execution, and human-in-the-loop escalation are rejected
  for this simulation.
- **Q: How is scoring eligibility reported when route qualification and service
  reroute evidence disagree?** **A:** Report route qualification and score
  eligibility as separate fields. A qualified plugin route is not
  scoring-eligible when unapproved service reroute evidence is present; an
  approved service reroute can preserve eligibility only when the final route is
  otherwise qualified and treatment immutability is proven.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve preferred and fallback routes deterministically (Priority: P1)

G56R-006 maintainers can resolve fixture policies through preferred and fallback routes and receive a byte-stable ordered diagnostic record with exactly one terminal outcome, without depending on live model availability.

**Why this priority**: This is the frozen contract G56R-006 needs before any production route policy can be installed.

**Independent Test**: Can be tested by replaying only fixture policies that cover preferred-route absence, fallback qualification, effort mismatch, and discovery failure, then comparing the emitted diagnostics and terminal outcome to approved expectations.

**Acceptance Scenarios**:

1. **Given** a fixture policy whose preferred model is absent and whose first fallback is qualified, **When** the resolver evaluates the policy, **Then** it records the preferred absence reason before the fallback qualification reason and ends with the fallback route as the only terminal outcome.
2. **Given** a fixture policy whose preferred route names an unsupported effort level, **When** a fallback route with an allowed effort level qualifies, **Then** the resolver records the effort mismatch and selects only the qualified fallback route.
3. **Given** a fixture policy whose discovery evidence is unavailable, **When** no fallback route can be safely qualified, **Then** the resolver records discovery unavailability and ends with a no-safe-route outcome.
4. **Given** exact invocation availability-probe evidence that succeeds, **When** the route is otherwise qualified, **Then** the resolver includes that probe evidence in the ordered diagnostics and treats the route as eligible for the terminal success outcome.
5. **Given** exact invocation availability-probe evidence that fails, **When** fallbacks remain available, **Then** the resolver records the probe failure before considering the next fallback route.
6. **Given** treatment-probe evidence that fails after availability has been proven, **When** the resolver evaluates scoring eligibility, **Then** it records the treatment-probe failure as a route qualification failure and does not report a successful route.

---

### User Story 2 - Attribute service reroutes separately from plugin reasons (Priority: P2)

Evaluation maintainers can replay approved and unapproved service reroutes and see service-originated evidence separated from plugin-originated reasons, with scoring eligibility determined from the approved evidence path.

**Why this priority**: Route evaluation must distinguish local plugin decisions from service reroute behavior so review and scoring do not misattribute availability or failure reasons.

**Independent Test**: Can be tested by replaying only service-reroute fixtures and asserting the emitted attribution category, reason ordering, score eligibility, and terminal outcome.

**Acceptance Scenarios**:

1. **Given** an approved service reroute fixture, **When** the resolver evaluates the reroute evidence, **Then** it records service reroute attribution separately from plugin reasons and preserves scoring eligibility when the final route is qualified.
2. **Given** an unapproved service reroute fixture, **When** the resolver evaluates the reroute evidence, **Then** it records the reroute as unapproved service evidence and marks the route ineligible for a successful terminal outcome.
3. **Given** a fixture with both service reroute evidence and plugin fallback reasons, **When** diagnostics are emitted, **Then** the service attribution remains distinct and the plugin reasons keep their deterministic local order.
4. **Given** a fixture where treatment changes something other than model or effort, **When** the resolver evaluates the route, **Then** it rejects the mutation as non-route treatment mutation and does not substitute a generic route.
5. **Given** repeated replay of the same service-reroute fixture, **When** each replay completes, **Then** the attribution, reason list, score eligibility, and terminal outcome are identical every time.
6. **Given** a service reroute that points to a route not declared in the fixture policy, **When** the resolver evaluates it, **Then** it rejects the route as unqualified-adjacent evidence and preserves the original policy boundary.

---

### User Story 3 - Prove fake-home recovery and required-install safety (Priority: P3)

Release reviewers can exercise optional-helper degradation, strict override rejection, fallback exhaustion, rollback, atomic no-write, and previous-known-good preservation in fake homes before required Codex agent installation behavior is wired to production.

**Why this priority**: The simulation must prove that failures cannot partially replace a required Codex agent install or destroy the last known valid install state.

**Independent Test**: Can be tested by running only fake-home state fixtures and verifying final filesystem state, recovery diagnostics, and terminal outcomes without writing to a real user home.

**Acceptance Scenarios**:

1. **Given** an optional helper is unavailable and the fixture explicitly declares an independently qualified no-helper continuation, **When** the required-agent route resolves safely, **Then** the harness records optional-helper degradation, proves zero helper-route attempts with separate counters, and continues through the no-helper path.
2. **Given** an incompatible strict override, **When** the resolver evaluates the override, **Then** it rejects the override as terminal and never falls back to another route.
3. **Given** all declared fallbacks are exhausted, **When** the resolver reaches the final candidate, **Then** it records fallback exhaustion and reports no-safe-route without partial installation.
4. **Given** a fake home with a previous-known-good required install identified by a canonical content manifest, **When** a replacement fails after staging but before completion, **Then** rollback restores the exact path, content, mode, and role-classification manifest and the failed replacement is not promoted.
5. **Given** a fake home where validation fails before any managed file is touched, **When** the attempted operation exits, **Then** no install target is created or modified, rollback is not run, and the pre-state and final-state IDs are identical.
6. **Given** a fake home where a required install is partially materialized, **When** rollback runs, **Then** it restores or removes every touched managed file, runs bounded best-effort cleanup, preserves the rollback result regardless of cleanup outcome, and records `writes_state=false` only when the exact pre-state is restored.
7. **Given** a recovery fixture is replayed multiple times from the same canonical pre-state, **When** each replay completes, **Then** its canonical Recovery Record and final-state manifest are byte-identical and contain no absolute temporary roots, timestamps, inodes, or host-specific paths.

---

### User Story 4 - Enforce bounded non-recursive harness execution (Priority: P4)

Cross-platform maintainers can run one sequential harness state machine that enforces retry, time, fan-out, context, cancellation, and escalation bounds while rejecting loops, inherited model or effort, unqualified-adjacent substitutions, and generic substitutions.

**Why this priority**: The harness must be bounded and fail-closed so simulation evidence is deterministic and cannot hide unbounded or interactive behavior.

**Independent Test**: Can be tested by replaying only harness-budget fixtures and asserting that every budget breach terminates predictably with no recursion, no human-in-the-loop escalation, and no unbounded fan-out.

**Acceptance Scenarios**:

1. **Given** a fixture that exceeds the declared retry count, **When** the harness reaches the retry limit, **Then** it stops with a bounded-retry terminal outcome.
2. **Given** a fixture that exceeds the declared time budget, **When** the harness detects the breach, **Then** it records the time-bound failure and cancels remaining work.
3. **Given** a fixture that exceeds fan-out or context limits, **When** the harness evaluates the fixture, **Then** it rejects the fixture before route success can be reported.
4. **Given** cancellation is requested during a fake-home operation, **When** the harness observes cancellation, **Then** it stops sequential processing and performs only the bounded recovery action required to preserve fake-home state.
5. **Given** a fixture attempts escalation beyond the declared limit, **When** the harness evaluates the escalation path, **Then** it fails closed without invoking a human-in-the-loop or recursive agent path.
6. **Given** a fixture's sequential walk reaches a route that was already attempted, **When** the resolver observes the repeated route, **Then** it emits loop rejection without re-attempting or re-consulting the route and ends with no-safe-route; an unreachable later duplicate does not invalidate an earlier successful resolution.
7. **Given** a fixture inherits model or effort from a parent or adjacent route rather than declaring it locally, **When** the resolver evaluates the route, **Then** it rejects inherited model or effort and preserves the Codex-local reason vocabulary.

### Edge Cases

- Preferred model absent while multiple fallback routes remain qualified.
- Preferred effort unsupported but model availability evidence exists.
- Discovery unavailable before exact invocation probing can occur.
- Availability-probe success followed by treatment-probe failure.
- Approved service reroute that changes only model and effort.
- Unapproved service reroute that otherwise points to a valid route.
- Optional helper unavailable with a validated no-helper continuation path.
- Strict override incompatible with the local capability evidence.
- Fallback exhaustion after bounded retry attempts.
- Loop, generic substitution, unqualified-adjacent route, or inherited model and effort.
- Partial required installation, rollback, atomic no-write, and previous-known-good preservation.
- Cancellation or budget breach while fake-home recovery is still pending.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept fixture policies containing preferred routes, ordered fallback routes, local capability evidence, exact invocation probe outcomes, treatment probe outcomes, strict override settings, service reroute evidence, helper availability, and an explicit fake-home starting state plus harness-created temporary `fake_home_root`.
- **FR-002**: System MUST perform pure route resolution separately from fake-home state changes so route decisions can be replayed without writing to any filesystem target.
- **FR-003**: System MUST emit every applicable diagnostic in the Resolution Ordering Contract and exactly one terminal outcome, placed last, for every route resolution attempt.
- **FR-004**: System MUST treat preferred model absence, unsupported effort, discovery unavailability, availability-probe failure, and treatment-probe failure as distinct locally authored reasons.
- **FR-005**: System MUST qualify a route only when its declared model, declared effort, local capability evidence, availability probe, and treatment probe satisfy the fixture policy.
- **FR-006**: System MUST allow fallback routes to change only model and effort, MUST canonically compare and digest agent identity, instructions, tools, skills and MCP bindings, sandbox, mutation policy, and output contract, and MUST reject any fallback or treatment mutation whose non-route comparison differs.
- **FR-007**: System MUST reject incompatible strict overrides as terminal outcomes and MUST NOT evaluate fallback routes after a strict override rejection.
- **FR-008**: System MUST attribute service reroute evidence separately from plugin reasons and MUST distinguish approved service reroutes from unapproved service reroutes.
- **FR-009**: System MUST calculate scoring eligibility from qualified route evidence plus approved service reroute status, and MUST mark unapproved service reroutes as ineligible.
- **FR-010**: System MUST detect a loop only when the sequential walk reaches an already attempted route, MUST NOT re-attempt or re-consult that route, and MUST reject loop, unqualified-adjacent, generic substitution, inherited model, and inherited effort cases fail-closed; fallback exhaustion MUST be diagnostic evidence or terminal details under the sole terminal `no_safe_route` outcome rather than a second terminal outcome.
- **FR-011**: System MUST record optional-helper unavailability and continue only when the fixture explicitly declares an independently qualified no-helper continuation; the replay MUST prove zero helper-route attempts with helper counters separate from required-route counters and MUST still prove required-agent success or atomic failure.
- **FR-012**: System MUST enforce declared retry limits and record bounded-retry exhaustion before any unbounded retry behavior can occur.
- **FR-013**: System MUST enforce declared time, fan-out, context, cancellation, and escalation budgets for every harness run.
- **FR-014**: System MUST use one non-recursive sequential harness state machine for simulation replay and MUST NOT invoke human-in-the-loop scoping or recursive agent execution.
- **FR-015**: System MUST apply fake-home state changes only through a staged adapter whose sole writable destination is the resolved `<fake_home_root>/.codex/agents`; it MUST reject real homes, checked-in fixture mutation, traversal, symlink traversal, or any destination outside that boundary, and MUST prove atomic no-write, rollback, and final-state preservation.
- **FR-016**: System MUST detect partial required Codex agent installation in fake homes; a failure before any managed file is touched MUST prove atomic no-write without rollback, while a failure, verification failure, or cancellation after a managed file is touched MUST trigger rollback followed by bounded best-effort cleanup.
- **FR-017**: System MUST identify pre-state and previous-known-good state from a canonical manifest of sorted fake-home-relative paths, SHA-256 content digests, file modes, and required/optional role classification; successful rollback MUST restore that exact manifest and report `writes_state=false`, while failed rollback MUST report `writes_state=true` with deterministic manual-remediation evidence, and cleanup MUST NOT replace the rollback or terminal result.
- **FR-018**: System MUST produce byte-stable canonical JSON replay and Recovery Records for the same fixture inputs, including reason order, attribution category, score eligibility, terminal outcome, pre-state and final-state IDs, deterministic staged/applied/rolled-back/cleanup action arrays, sorted cleanup errors, rollback outcome, write-state disposition, manual remediation, and final fake-home state; records MUST exclude absolute temporary roots, mtimes, inodes, timestamps, and host-specific paths.
- **FR-019**: System MUST preserve frozen Claude and G56R-004 behavior by keeping the Codex resolver and reason vocabulary locally authoritative without importing Claude logic or extracting a shared resolver core.
- **FR-020**: System MUST avoid live model or service qualification claims and MUST NOT wire production resolver, installer, payload, version, release artifact, checkpoint, or resume behavior in this feature.
- **FR-021**: System MUST cover every scenario listed in the Required Scenario Coverage section with at least one independently replayable fixture or acceptance case.
- **FR-022**: System MUST provide review evidence that maps each major requirement and success criterion to fixture coverage, replay output, and any fake-home state assertion.

### Resolution Ordering Contract

1. Evaluate strict override compatibility before any route walk. An incompatible
   override stops before writes or fallback evaluation and emits the strict
   override rejection as its sole terminal outcome.
2. When no incompatible strict override stops evaluation, visit the preferred
   route and then each declared fallback in fixture order.
3. For each reached route, emit all applicable reasons in this fixed order:
   model absence, unsupported effort, capability-discovery unavailability,
   availability-probe failure, treatment-probe failure, and non-route treatment
   mutation.
4. Detect a loop when the walk reaches a route already attempted. Emit loop
   rejection without re-attempting or re-consulting that route. A duplicate that
   is never reached cannot invalidate an earlier successful resolution.
5. Emit exactly one terminal outcome last. When every reachable declared route
   is exhausted, record exhaustion in diagnostic evidence or terminal details
   and use `no_safe_route` as the sole terminal outcome.

### Required Scenario Coverage

- Preferred model absent; effort unsupported; discovery unavailable.
- Exact invocation availability-probe success; exact invocation availability-probe failure; treatment-probe failure.
- Approved service reroute; unapproved service reroute; no safe route.
- Optional helper unavailable; validated no-helper continuation; incompatible strict override; bounded retry; fallback exhaustion.
- Loop rejection; unqualified-adjacent rejection; generic substitution rejection; inherited model rejection; inherited effort rejection.
- Partial required installation; non-route treatment mutation rejection.
- Atomic no-write; rollback; previous-known-good preservation; cancellation;
  fake-home boundary escape, traversal, and symlink rejection.
- Retry, time, fan-out, context, cancellation, and escalation budget enforcement.

### Reviewability Notes *(if applicable)*

- This feature is repository-local simulation evidence only. It must not install real route policies, change shipped payloads, or publish live model availability claims.
- Typed reviewability exceptions are not expected. If planning discovers a required exception, it must be recorded before implementation with operator ownership and a narrow scope.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: seed/config and docs/process
- **Projected reviewable LOC**: 900 non-generated LOC
- **Projected production files**: 0
- **Projected total files**: 10
- **Budget result**: within budget
- **Split decision**: Remains one spec because the work is a bounded simulation contract with one resolver vocabulary, one fake-home adapter boundary, and one sequential harness state machine. Production G56R-006 wiring remains a separate follow-up.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Review packet MUST explicitly state that live model or service qualification was not performed.
- Review packet MUST show that generated payloads, plugin versions, production routing, and frozen Claude/G56R-004 behavior were not modified.
- Review packet MUST include fake-home recovery evidence for partial required install, rollback, cleanup, atomic no-write, previous-known-good preservation, boundary rejection, canonical state IDs, and the absence of host-specific paths or metadata.

### Key Entities *(include if feature involves data)*

- **Fixture Policy**: A deterministic policy record that declares preferred route, fallback route order, strict override status, allowed route mutations, helper availability, any explicit independently qualified no-helper continuation, service reroute evidence, and fake-home starting state.
- **Route Candidate**: A declared model and effort pairing with local qualification evidence, probe outcomes, and canonical digest evidence for every non-route treatment field.
- **Diagnostic Reason**: A locally authored Codex reason that explains why a route was qualified, rejected, or skipped and occupies its fixed position in the Resolution Ordering Contract.
- **Terminal Outcome**: The single final result emitted last for a resolution attempt, such as qualified route, strict override rejected, bounded retry exhausted, or no safe route; fallback exhaustion is evidence or details under no-safe-route, not a second terminal outcome.
- **Service Reroute Evidence**: Attribution record for externally observed reroute behavior, separated from plugin-authored reasons and marked approved or unapproved.
- **Score Eligibility Record**: Deterministic decision explaining whether a replay can contribute to scoring based on route qualification and service reroute approval.
- **Harness Budget**: Declared retry, time, fan-out, context, cancellation, and escalation limits for a sequential replay.
- **Fake Home State**: Isolated filesystem representation rooted at an explicit harness-created temporary directory, identified by a canonical manifest of sorted relative paths, content digests, modes, and role classifications; its only writable destination is `.codex/agents` beneath that root.
- **Previous-Known-Good Install**: The last validated fake-home install state, identified by the canonical state manifest rather than host filesystem metadata, that must remain exactly recoverable if a replacement fails.
- **Recovery Record**: Closed canonical JSON evidence containing pre-state and final-state IDs, deterministic staged/applied/rolled-back/cleanup action arrays, sorted cleanup errors, rollback outcome, write-state disposition, manual remediation, and cancellation handling without absolute temporary paths or host-specific metadata.

### Local Capability Evidence

- Human decisions: `docs/ai/specs/.process/G56R-005-design-concept.md`
- Roadmap dependency: `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- Constitution constraints: `.specify/memory/constitution.md`
- Existing Codex capability contracts and fixture precedent: `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/`
- Existing Codex qualification behavior: `tests/speckit-pro/unit/test-codex-qualification-contracts.py`
- Existing route fallback simulation precedent: `tests/speckit-pro/unit/test-route-fallback-simulation.py`
- Existing Claude fallback precedent to preserve, not import: `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py`
- Existing fallback scenario corpus precedent: `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json`
- Existing fake-home and atomicity precedent: `tests/speckit-pro/unit/fixtures/atomicity-route/`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of required scenario coverage rows are represented by at least one independently replayable acceptance case or fixture.
- **SC-002**: Replaying the same fixture inputs three consecutive times produces byte-identical canonical records for reason order, attribution category, score eligibility, terminal outcome, recovery actions, pre-state and final-state IDs, and fake-home final state, with zero absolute temporary roots or host-specific metadata.
- **SC-003**: 100% of resolution attempts produce diagnostics in the Resolution Ordering Contract order, exactly one terminal outcome emitted last, and zero ambiguous terminal states; every exhausted fallback walk ends only in `no_safe_route`.
- **SC-004**: 100% of strict override rejection cases stop without fallback evaluation.
- **SC-005**: 100% of service reroute cases report service attribution separately from plugin reasons and mark approved versus unapproved status.
- **SC-006**: 100% of fake-home failure cases either preserve the exact canonical previous-known-good manifest or prove atomic no-write when no managed file was touched; rollback failures report `writes_state=true` and manual remediation, cleanup never masks rollback, and every no-helper continuation proves an explicit independent qualification, zero helper-route attempts, separate counters, and required-agent success or atomic failure.
- **SC-007**: 100% of retry, time, fan-out, context, cancellation, and escalation budget fixtures terminate at the declared bound with no recursive or human-in-the-loop path.
- **SC-008**: Reviewers can trace every functional requirement to scenario coverage and verification evidence within the PR packet.
- **SC-009**: Final review finds zero production route policy changes, zero live model availability claims, zero generated payload changes, and zero frozen Claude/G56R-004 contract edits.

## Assumptions

- G0 baseline is 7659/7659 before this Phase 1 specification, and parent validation owns any broader gate execution after the phase completes.
- "Availability" and "service reroute" mean deterministic local fixture evidence only; this feature makes no live model, service, provider, or runtime claim.
- "Required Codex agent install" means a fake-home representation of required install outputs, not a real user home or production installer target.
- Checked-in fake-home fixtures are immutable seeds. Every mutation replay copies
  its pre-state into an explicit harness-created temporary root and may write
  only beneath that root's `.codex/agents` directory.
- "Score eligibility" means eligibility for local evaluation scoring, not an external service score.
- Existing Claude fallback behavior remains frozen and is used only as preservation evidence and precedent; Codex reason vocabulary remains locally authoritative.
- Production resolver wiring, installer wiring, payload regeneration, version changes, release artifacts, checkpoint scheduling, and resume scheduling are deferred to later specs.
