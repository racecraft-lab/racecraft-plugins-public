# Feature Specification: PRSG-010 Harden the Hatch + O5 Monster Epics

**Feature Branch**: `prsg-010-harden-the-hatch`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "PRSG-010 hardens the final reviewability backstop, removes generated exception boilerplate, adds an O5 monster-epic parent/child model, and promotes contextual routing probes only when evidence is deterministic and high confidence."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop Unreviewable PRs Before Creation (Priority: P1)

Maintainers reviewing speckit-pro-generated work need the final reviewability gate to be a real backstop. When the final diff gate blocks and no valid typed exception exists, autopilot must stop before PR creation and record enough re-slicing guidance for the operator to continue through the existing sizing, routing, layer planning, and multi-PR flow.

**Why this priority**: This is the remaining hatch that can let oversized PRs reach reviewers. It protects reviewer time and keeps PRSG-007, PRSG-008, and PRSG-009 enforceable at the last boundary.

**Independent Test**: Can be tested by running an autopilot completion scenario where the final gate blocks without a valid exception and confirming no PR is created while a re-slicing packet is recorded.

**Acceptance Scenarios**:

1. **Given** the final diff gate reports a blocking reviewability result and no valid typed exception is present, **When** autopilot reaches the final PR creation boundary, **Then** it stops before any PR creation action and records a blocked gate outcome.
2. **Given** a blocking reviewability result has an explicit operator-owned `Reviewability-Exception: refactor`, `Reviewability-Exception: infra`, or `Reviewability-Exception: upgrade`, **When** autopilot evaluates the final gate, **Then** the typed exception is honored and recorded as the reason the run may proceed.
3. **Given** generated roadmap, template, or boilerplate content contains exception-like text, **When** the final gate evaluates exception evidence, **Then** that generated text does not count as an operator-owned exception and the unexcepted block path remains active.

---

### User Story 2 - Model Genuine Monster Epics Without Nested Specs (Priority: P2)

Spec authors need an O5 parent/child model for genuinely large efforts that cannot fit the normal O4 split path. The model must let a parent manifest coordinate flat sibling child specs, shared design concept and retrospective links, dependency order, and deterministic status rollup without introducing nested `specs/<parent>/<child>` scanning.

**Why this priority**: Some roadmap items are too large for a single ordinary split plan, but the fallback must preserve navigability and avoid a broad tree-shape rewrite.

**Independent Test**: Can be tested by creating a parent manifest with flat sibling child specs and confirming scaffold/status surfaces the parent, children, dependency order, shared links, and rollup state deterministically.

**Acceptance Scenarios**:

1. **Given** an O5 parent manifest lists flat sibling child specs with dependency order, **When** status is requested for the parent, **Then** the rollup lists the children in a stable order with each child's current phase and blocking state.
2. **Given** O5 child specs link to the parent manifest plus shared design concept and retrospective references, **When** spec navigation or index generation runs, **Then** the links remain navigable without scanning nested child directories.
3. **Given** an O5 parent or child has missing, duplicate, circular, or unsupported topology data, **When** scaffold or status validates the O5 model, **Then** it reports an actionable problem instead of silently producing an incorrect rollup.

---

### User Story 3 - Route From Strong Contextual Evidence Only (Priority: P3)

Maintainers of the atomicity router need flag-system, release-cadence, and consumer-locality probes to affect routing only when the evidence is deterministic and high confidence. Weak or shallow evidence must stay advisory so the router remains conservative.

**Why this priority**: Better contextual routing reduces unnecessary blocks and helps operators choose a safer split shape, but speculative signals could misroute work.

**Independent Test**: Can be tested with fixture-backed routing cases where high-confidence evidence changes the route and weak evidence leaves the existing conservative route unchanged.

**Acceptance Scenarios**:

1. **Given** deterministic evidence proves a flag-system, release-cadence, or consumer-locality boundary, **When** the router evaluates the work, **Then** it may emit a decisive routing signal using the documented signal vocabulary.
2. **Given** evidence is only a shallow keyword hit, stale reference, comment, code-fence example, or unrelated fixture, **When** the router evaluates the work, **Then** it preserves the existing conservative route and records at most an advisory hint.
3. **Given** contextual evidence conflicts or cannot be tied to the current change, **When** the router evaluates the work, **Then** it records the uncertainty as a warning or hint rather than a decisive route reason.

---

### Edge Cases

- Final gate blocks after verification evidence exists but before PR creation has happened.
- Final gate blocks on a resume after a previous run already wrote partial local PR body or state artifacts.
- A typed exception is present with an invalid class, mixed casing, trailing prose, or generated-template provenance.
- A valid typed exception is present for one slice but the current oversized diff belongs to a different slice.
- Generated templates mention exceptions for education but must not include a ready-to-copy override line.
- An O5 parent manifest lists zero children, missing children, duplicate child identifiers, or children that no longer exist.
- O5 child dependencies form a cycle or refer to a child outside the parent manifest.
- Status rollup encounters mixed child states such as completed, blocked, archived, and pending in the same parent.
- Contextual probes match code fences, comments, fixtures, sample docs, or unrelated historical specs.
- Contextual probes find strong evidence for one boundary but weak evidence for another in the same task set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Autopilot MUST run the final reviewability diff gate after implementation verification and before any action that creates or updates a pull request for the current feature.
- **FR-002**: When the final diff gate returns a blocking result and no valid typed exception exists, autopilot MUST stop before PR creation.
- **FR-003**: A valid exception MUST be limited to an explicit operator-owned `Reviewability-Exception: refactor`, `Reviewability-Exception: infra`, or `Reviewability-Exception: upgrade` entry.
- **FR-004**: Generated roadmap, workflow, template, and PR-description content MUST NOT include live copy-pasteable exception boilerplate that can be mistaken for an operator-owned override.
- **FR-005**: The unexcepted block path MUST record the gate result, gate reason, review surface metrics, exception status, blocked operation, and timestamp in the run state.
- **FR-006**: The unexcepted block path MUST produce a re-slicing packet that names the feature, the failed gate evidence, the relevant PRSG-007 sizing result, PRSG-008 layer-planning route, PRSG-009 multi-PR handoff, suggested slice boundaries, and resume guidance.
- **FR-007**: The blocked run state MUST make clear that no pull request URL, number, or head/base PR record was created for the blocked operation.
- **FR-008**: Status surfaces MUST show the final gate block as an actionable re-slicing state rather than as an advisory warning.
- **FR-009**: When a valid typed exception is honored, the run state and review packet MUST record the exception class, provenance, and gate result that required the exception.
- **FR-010**: Scaffold/status flows MUST support an O5 parent manifest reserved for monster epics that cannot fit the normal O4 split path.
- **FR-011**: The O5 parent manifest MUST capture parent identifier, title, child spec identifiers, flat child paths, dependency order, shared design concept link, shared retrospective link, and current rollup status.
- **FR-012**: O5 child specs MUST remain flat siblings under `specs/` and MUST link back to their O5 parent manifest.
- **FR-013**: O5 v1 MUST NOT require or introduce nested `specs/<parent>/<child>` scanning.
- **FR-014**: O5 validation MUST detect missing child specs, duplicate child identifiers, unsupported nested child paths, and circular dependency order.
- **FR-015**: Status rollup for an O5 parent MUST be deterministic across repeated runs and MUST preserve the declared child dependency order.
- **FR-016**: PRSG-010 MUST NOT migrate old specs into the O5 model.
- **FR-017**: Atomicity routing MUST evaluate flag-system, release-cadence, and consumer-locality evidence as contextual probes with explicit high-confidence criteria.
- **FR-018**: Contextual probes MUST become decisive routing signals only when deterministic evidence meets the high-confidence criteria for the specific probe.
- **FR-019**: Weak, stale, ambiguous, fixture-only, or shallow keyword evidence MUST preserve the existing conservative route and may only appear as an advisory hint or warning.
- **FR-020**: PRSG-010 delivery MUST be planned as an ordered split-PR stack unless the router classifies the final task plan otherwise.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process, seed/config
- **Projected reviewable LOC**: 1,700 total before slicing; each implementation slice should target 700 or fewer reviewable LOC
- **Projected production files**: 8
- **Projected total files**: 28
- **Budget result**: split required
- **Split decision**: Keep one PRSG-010 governing spec, but require implementation planning as an ordered stack: hatch backstop, O5 parent/child support, contextual routing probes, then docs/parity/polish.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Final Gate Result**: The reviewability decision recorded at the last boundary before PR creation, including status, metrics, reason, and exception evaluation.
- **Reviewability Exception**: An explicit operator-owned typed override using one of the preserved classes: refactor, infra, or upgrade.
- **Re-slicing Packet**: The actionable recovery artifact written when an oversized unexcepted diff is blocked before PR creation.
- **O5 Parent Manifest**: A monster-epic coordination record that lists flat sibling child specs, dependency order, shared links, and rollup status.
- **O5 Child Spec**: A normal flat spec directory linked to an O5 parent manifest and ordered relative to its sibling child specs.
- **Contextual Probe Evidence**: Deterministic observations used to decide whether flag-system, release-cadence, or consumer-locality context is strong enough to affect routing.
- **Routing Decision**: The final atomicity-route outcome that distinguishes decisive signals, advisory hints, warnings, and conservative fallback behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of final gate block scenarios without a valid typed exception, no pull request is created and a re-slicing packet is recorded.
- **SC-002**: In 100% of valid typed exception scenarios, the exception class and provenance are visible in run state and review evidence.
- **SC-003**: Generated workflow, roadmap, and template artifacts contain zero live copy-pasteable exception override lines.
- **SC-004**: A maintainer can identify the next re-slicing action from a blocked run in under 5 minutes using the recorded packet and status output.
- **SC-005**: O5 parent rollup output is stable across repeated runs for the same parent/child inputs.
- **SC-006**: Contextual probe fixtures demonstrate that weak evidence changes the decisive route 0% of the time, while high-confidence evidence uses the documented signal vocabulary 100% of the time.

## Assumptions

- PRSG-007 sizing, PRSG-008 layer planning, and PRSG-009 multi-PR emission remain the normal split path and are available for PRSG-010 recovery guidance.
- O5 is a reserved fallback for genuine monster epics after ordinary split planning is insufficient; it is not a replacement for O4 split work.
- Operators can still provide explicit typed exceptions, but generated content must not supply reusable exception text.
- Flat `specs/` directory scanning remains authoritative for v1 navigation, MOC/index behavior, and status discovery.
- PRSG-010 implementation will use the repository's deterministic validation layers for any changed scripts, skills, fixtures, templates, or docs.
