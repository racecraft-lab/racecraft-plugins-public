# Feature Specification: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Feature Branch**: `g56r-005-model-availability-fallback-recovery`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "G56R-005 Model Availability, Fallback, and Recovery Simulation"

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

1. **Given** an optional helper is unavailable, **When** a validated no-helper route remains safe, **Then** the harness records optional-helper degradation and continues through the no-helper path.
2. **Given** an incompatible strict override, **When** the resolver evaluates the override, **Then** it rejects the override as terminal and never falls back to another route.
3. **Given** all declared fallbacks are exhausted, **When** the resolver reaches the final candidate, **Then** it records fallback exhaustion and reports no-safe-route without partial installation.
4. **Given** a fake home with a previous-known-good required install, **When** a replacement fails after staging but before completion, **Then** the previous-known-good install remains available and the failed replacement is not promoted.
5. **Given** a fake home where atomic no-write validation fails before staging, **When** the attempted operation exits, **Then** no required install target is created or modified.
6. **Given** a fake home where a required install is partially materialized, **When** rollback runs, **Then** all partial required-install artifacts are removed and the recovery record names the rollback outcome.
7. **Given** a recovery fixture is replayed multiple times, **When** each replay starts from the same fake-home state, **Then** the final fake-home state and diagnostics remain byte-stable.

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
6. **Given** a fixture introduces a loop, generic substitution, or unqualified-adjacent substitution, **When** the resolver evaluates the candidate, **Then** it rejects the candidate before fallback success can be reported.
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

- **FR-001**: System MUST accept fixture policies containing preferred routes, ordered fallback routes, local capability evidence, exact invocation probe outcomes, treatment probe outcomes, strict override settings, service reroute evidence, helper availability, and fake-home starting state.
- **FR-002**: System MUST perform pure route resolution separately from fake-home state changes so route decisions can be replayed without writing to any filesystem target.
- **FR-003**: System MUST emit ordered applicable reasons plus exactly one terminal outcome for every route resolution attempt.
- **FR-004**: System MUST treat preferred model absence, unsupported effort, discovery unavailability, availability-probe failure, and treatment-probe failure as distinct locally authored reasons.
- **FR-005**: System MUST qualify a route only when its declared model, declared effort, local capability evidence, availability probe, and treatment probe satisfy the fixture policy.
- **FR-006**: System MUST allow fallback routes to change only model and effort, and MUST reject any fallback or treatment mutation that changes a non-route property.
- **FR-007**: System MUST reject incompatible strict overrides as terminal outcomes and MUST NOT evaluate fallback routes after a strict override rejection.
- **FR-008**: System MUST attribute service reroute evidence separately from plugin reasons and MUST distinguish approved service reroutes from unapproved service reroutes.
- **FR-009**: System MUST calculate scoring eligibility from qualified route evidence plus approved service reroute status, and MUST mark unapproved service reroutes as ineligible.
- **FR-010**: System MUST reject no-safe-route, fallback exhaustion, loop, unqualified-adjacent, generic substitution, inherited model, and inherited effort cases as fail-closed outcomes.
- **FR-011**: System MUST record optional-helper unavailability and continue only when a validated no-helper continuation path is declared by the fixture.
- **FR-012**: System MUST enforce declared retry limits and record bounded-retry exhaustion before any unbounded retry behavior can occur.
- **FR-013**: System MUST enforce declared time, fan-out, context, cancellation, and escalation budgets for every harness run.
- **FR-014**: System MUST use one non-recursive sequential harness state machine for simulation replay and MUST NOT invoke human-in-the-loop scoping or recursive agent execution.
- **FR-015**: System MUST apply fake-home state changes only through a staged adapter that can prove atomic no-write, rollback, and final-state preservation.
- **FR-016**: System MUST detect partial required Codex agent installation in fake homes and restore the previous-known-good install state when replacement cannot complete safely.
- **FR-017**: System MUST preserve a previous-known-good fake-home install when a new required install attempt fails before promotion.
- **FR-018**: System MUST produce byte-stable replay records for the same fixture inputs, including reason order, attribution category, score eligibility, terminal outcome, and final fake-home state.
- **FR-019**: System MUST preserve frozen Claude and G56R-004 behavior by keeping the Codex resolver and reason vocabulary locally authoritative without importing Claude logic or extracting a shared resolver core.
- **FR-020**: System MUST avoid live model or service qualification claims and MUST NOT wire production resolver, installer, payload, version, release artifact, checkpoint, or resume behavior in this feature.
- **FR-021**: System MUST cover every scenario listed in the Required Scenario Coverage section with at least one independently replayable fixture or acceptance case.
- **FR-022**: System MUST provide review evidence that maps each major requirement and success criterion to fixture coverage, replay output, and any fake-home state assertion.

### Required Scenario Coverage

- Preferred model absent; effort unsupported; discovery unavailable.
- Exact invocation availability-probe success; exact invocation availability-probe failure; treatment-probe failure.
- Approved service reroute; unapproved service reroute; no safe route.
- Optional helper unavailable; validated no-helper continuation; incompatible strict override; bounded retry; fallback exhaustion.
- Loop rejection; unqualified-adjacent rejection; generic substitution rejection; inherited model rejection; inherited effort rejection.
- Partial required installation; non-route treatment mutation rejection.
- Atomic no-write; rollback; previous-known-good preservation; cancellation.
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
- Review packet MUST include fake-home recovery evidence for partial required install, rollback, atomic no-write, and previous-known-good preservation.

### Key Entities *(include if feature involves data)*

- **Fixture Policy**: A deterministic policy record that declares preferred route, fallback route order, strict override status, allowed route mutations, helper availability, service reroute evidence, and fake-home starting state.
- **Route Candidate**: A declared model and effort pairing with local qualification evidence and probe outcomes.
- **Diagnostic Reason**: A locally authored Codex reason that explains why a route was qualified, rejected, skipped, or terminated.
- **Terminal Outcome**: The single final result for a resolution attempt, such as qualified route, strict override rejected, bounded retry exhausted, fallback exhausted, or no safe route.
- **Service Reroute Evidence**: Attribution record for externally observed reroute behavior, separated from plugin-authored reasons and marked approved or unapproved.
- **Score Eligibility Record**: Deterministic decision explaining whether a replay can contribute to scoring based on route qualification and service reroute approval.
- **Harness Budget**: Declared retry, time, fan-out, context, cancellation, and escalation limits for a sequential replay.
- **Fake Home State**: Isolated filesystem representation used to prove required Codex agent install safety without touching a real user home.
- **Previous-Known-Good Install**: The last validated fake-home install state that must remain recoverable if a replacement fails.
- **Recovery Record**: Deterministic evidence for atomic no-write, rollback, previous-known-good preservation, and cancellation handling.

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
- **SC-002**: Replaying the same fixture inputs three consecutive times produces identical reason order, attribution category, score eligibility, terminal outcome, and fake-home final state.
- **SC-003**: 100% of resolution attempts produce exactly one terminal outcome and zero ambiguous terminal states.
- **SC-004**: 100% of strict override rejection cases stop without fallback evaluation.
- **SC-005**: 100% of service reroute cases report service attribution separately from plugin reasons and mark approved versus unapproved status.
- **SC-006**: 100% of fake-home failure cases preserve previous-known-good state or prove atomic no-write when no prior state exists.
- **SC-007**: 100% of retry, time, fan-out, context, cancellation, and escalation budget fixtures terminate at the declared bound with no recursive or human-in-the-loop path.
- **SC-008**: Reviewers can trace every functional requirement to scenario coverage and verification evidence within the PR packet.
- **SC-009**: Final review finds zero production route policy changes, zero live model availability claims, zero generated payload changes, and zero frozen Claude/G56R-004 contract edits.

## Assumptions

- G0 baseline is 7659/7659 before this Phase 1 specification, and parent validation owns any broader gate execution after the phase completes.
- "Availability" and "service reroute" mean deterministic local fixture evidence only; this feature makes no live model, service, provider, or runtime claim.
- "Required Codex agent install" means a fake-home representation of required install outputs, not a real user home or production installer target.
- "Score eligibility" means eligibility for local evaluation scoring, not an external service score.
- Existing Claude fallback behavior remains frozen and is used only as preservation evidence and precedent; Codex reason vocabulary remains locally authoritative.
- Production resolver wiring, installer wiring, payload regeneration, version changes, release artifacts, checkpoint scheduling, and resume scheduling are deferred to later specs.
