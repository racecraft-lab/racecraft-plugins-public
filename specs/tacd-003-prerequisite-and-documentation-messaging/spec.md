# Feature Specification: Prerequisite and Documentation Messaging

**Feature Branch**: `tacd-003-prerequisite-and-documentation-messaging`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "Prerequisite and Documentation Messaging"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-blocking Capability Advisory (Priority: P1)

As a SpecKit Pro user running autopilot without optional research or context
capabilities installed, I want prerequisite checks to tell me when capability
coverage may affect confidence without blocking setup when an acceptable
fallback exists.

**Why this priority**: This is the most direct user-facing setup behavior. A
missing optional capability should not be presented as a failed contract when
the workflow can still proceed with fallbacks.

**Independent Test**: Can be tested by running prerequisite validation in an
environment without optional research or context capabilities and confirming the
result remains successful while the advisory explains confidence and fallback
behavior.

**Acceptance Scenarios**:

1. **Given** optional research or context capabilities are absent but fallback
   behavior is available, **When** the prerequisite check runs, **Then** setup
   succeeds and shows a generic non-blocking capability advisory.
2. **Given** optional research or context capabilities are absent, **When** the
   prerequisite check reports advisory output, **Then** the output avoids
   presenting a fixed named optional-tool set as a setup requirement.

---

### User Story 2 - Capability-first User Guidance (Priority: P2)

As a SpecKit Pro user reading prerequisite, limitation, coach, or autopilot
guidance, I want tool-agnostic capability guidance so I understand fallback
behavior without being told to install a fixed optional-tool set.

**Why this priority**: Documentation must match the capability-discovery
behavior delivered by TACD-002 so users with different installed tools receive
accurate expectations.

**Independent Test**: Can be tested by reviewing active user guidance and
confirming it describes capability discovery, confidence impact, and fallback
behavior without fixed optional-tool installation guidance.

**Acceptance Scenarios**:

1. **Given** a user reads active prerequisite or limitation guidance, **When**
   optional research or context coverage is described, **Then** the guidance
   explains capability-first discovery and fallback behavior.
2. **Given** a user has stronger optional capabilities installed, **When** they
   read active coach or autopilot guidance, **Then** the guidance makes clear
   that discovery should use available capabilities rather than vendor-specific
   preference.

---

### User Story 3 - Focused Regression Coverage (Priority: P3)

As a maintainer, I want focused deterministic coverage for changed prerequisite
output or active documentation assertions so TACD-003 does not regress before
TACD-004 adds broader enforcement.

**Why this priority**: Maintainers need targeted confidence for this slice
without expanding into the broader static or eval enforcement owned by TACD-004.

**Independent Test**: Can be tested by running the focused deterministic checks
that cover changed prerequisite output or active guidance assertions, then
running the existing structural and default verification commands.

**Acceptance Scenarios**:

1. **Given** prerequisite output changes, **When** deterministic coverage runs,
   **Then** the expected generic advisory is verified and fixed optional-tool
   reporting is rejected for the changed output.
2. **Given** active guidance changes, **When** deterministic coverage runs,
   **Then** changed active documentation assertions are verified without
   requiring broad static or eval enforcement.

### Edge Cases

- Optional research and context capabilities are missing, but local fallbacks
  can still support the workflow with reduced confidence.
- Optional research and context capabilities are present, and guidance must not
  reduce them to a hardcoded vendor preference.
- Active guidance needs an exact repository file reference, platform metadata
  label, or historical provenance reference that may include concrete names.
- Historical archives, changelogs, fixtures, or provenance records contain
  fixed-tool examples that are not active user guidance.
- Generated payloads contain stale wording and require source-backed
  regeneration rather than direct hand edits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Prerequisite checking MUST replace the fixed named optional-tool
  report with a generic non-blocking advisory about research and context
  capability coverage.
- **FR-002**: Prerequisite checking MUST preserve successful setup when optional
  research or context capabilities are missing and an acceptable fallback path
  exists.
- **FR-003**: The advisory MUST explain that missing optional capability
  coverage may reduce confidence or require fallback behavior without presenting
  the missing capability as a hard setup failure.
- **FR-004**: Active prerequisite and limitation guidance MUST explain
  capability-first discovery and fallback behavior in user-facing language.
- **FR-005**: Active coach and autopilot guidance MUST align with TACD-002
  behavior by directing agents and users toward capability discovery rather than
  a hardcoded optional-tool contract.
- **FR-006**: Active guidance MUST avoid concrete optional tool identifiers
  except where they are platform metadata, exact file references, or historical
  provenance.
- **FR-007**: TACD-003 MUST NOT rework agent behavior already shipped by
  TACD-002, add installers, add marketplace integration, or introduce a new
  recommended optional-tool set.
- **FR-008**: TACD-003 MUST add or update focused deterministic coverage for the
  changed prerequisite output or active documentation assertions.
- **FR-009**: TACD-003 MUST leave broad static enforcement, final eval
  expectation changes, and broader fixed-tool detection to TACD-004.
- **FR-010**: Generated payloads MUST NOT be hand-edited unless a source change
  requires and documents the regeneration step.

### Reviewability Notes *(if applicable)*

- This spec is a narrow messaging and deterministic-coverage alignment slice.
  It intentionally excludes broad enforcement and behavior rewrites because
  those surfaces belong to TACD-002 or TACD-004.
- Historical archives, changelogs, and provenance records are not active user
  guidance and are excluded unless they are reused as current setup guidance.
- Concrete repository file references may appear in the implementation plan and
  PR packet for traceability, but active user-facing guidance should remain
  capability-first.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter
- **Projected reviewable LOC**: 250
- **Projected production files**: 6
- **Projected total files**: 9
- **Budget result**: within budget
- **Split decision**: Keep as one spec because the slice changes one
  prerequisite messaging path, a small set of active guidance references, and
  focused deterministic coverage. Any broader enforcement or eval rewrites are
  deferred to TACD-004.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name TACD-004 or another explicit follow-up spec or issue.
- The review packet MUST call out that missing optional research or context
  capabilities remain non-blocking when acceptable fallbacks exist.
- The review packet MUST identify any exact file references, platform metadata,
  or historical provenance that still contains concrete optional-tool names and
  explain why each is outside active guidance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a missing-optional-capability setup path with acceptable
  fallback coverage, prerequisite checking completes successfully and emits
  exactly one generic non-blocking capability advisory.
- **SC-002**: 100% of changed active prerequisite, limitation, coach, and
  autopilot guidance uses capability-first language for research and context
  support.
- **SC-003**: 0 changed active user-facing guidance passages introduce a fixed
  optional-tool installation contract, excluding platform metadata, exact file
  references, and historical provenance.
- **SC-004**: Focused deterministic coverage verifies the changed prerequisite
  output or active guidance assertions before implementation is considered
  complete.
- **SC-005**: Maintainers can review the TACD-003 PR within the declared budget
  using a traceability packet that maps every functional requirement to changed
  files and verification evidence.

## Assumptions

- TACD-002 has already shipped the shared capability-discovery directive for
  agent behavior, and TACD-003 only aligns prerequisite output and active
  guidance with that behavior.
- Missing optional research or context coverage can still have an acceptable
  fallback path, but the user should be told that confidence may be lower.
- Active guidance includes prerequisite, limitation, coach, and autopilot
  messaging that users or agents rely on during current workflows.
- Historical archive, changelog, fixture-only, and provenance references are
  not active guidance unless they are reused as current setup instructions.
- TACD-004 will own broader enforcement against fixed optional-tool guidance,
  including broad static checks or eval expectation changes.
