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
  can still support the workflow with reduced confidence; setup should continue
  with an advisory rather than fail.
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
  report with one generic non-blocking advisory about research and context
  capability coverage.
- **FR-002**: Prerequisite checking MUST preserve successful setup when optional
  research or context capabilities are missing and an acceptable fallback path
  exists.
- **FR-003**: The advisory MUST explain that missing optional capability
  coverage may reduce confidence or require fallback behavior without presenting
  the missing capability as a hard setup failure.
- **FR-004**: Active Claude and Codex prerequisite guidance MUST be treated as
  peer active prerequisite surfaces that express the same capability-first
  contract for codebase context, library documentation, web/domain research, and
  source extraction, including fallback and escalation behavior, in user-facing
  language. Active limitation guidance MUST align with that same contract.
- **FR-005**: Active coach and autopilot guidance MUST align with TACD-002
  behavior by directing agents and users toward capability discovery rather than
  a hardcoded optional-tool contract.
- **FR-006**: Active guidance MUST avoid concrete optional tool identifiers
  except where they are platform metadata, exact repository file references,
  generated source-derived duplicates, or historical provenance.
- **FR-007**: TACD-003 MUST NOT rework agent behavior already shipped by
  TACD-002, add installers, add marketplace integration, or introduce a new
  recommended optional-tool set.
- **FR-008**: TACD-003 MUST add or update focused deterministic Layer 4
  coverage for the changed prerequisite JSON output and narrow assertions for
  changed active guidance.
- **FR-009**: TACD-003 MUST leave broad static enforcement, final eval
  expectation changes, and broader fixed-tool detection to TACD-004.
- **FR-010**: Generated payloads MUST NOT be hand-edited unless a source change
  requires and documents the regeneration step.
- **FR-011**: Prerequisite output MUST expose the advisory as a successful
  `capability_coverage` check with no per-tool available/missing inventory.
- **FR-012**: Active prerequisite output and guidance MUST require user
  escalation only when no acceptable evidence path exists after fallback
  attempts or when a true prerequisite/gate fails; missing optional research or
  context capability coverage alone MUST remain advisory.
- **FR-013**: Prerequisite output MUST remain deterministic and
  machine-parseable for downstream consumers. Standard output MUST contain one
  JSON document with stable top-level fields for overall pass state, branch
  context, worktree context, feature-branch context, and checks; the changed
  `capability_coverage` advisory MUST retain stable check, pass, message, and
  detail fields. Diagnostic text for failures MUST NOT be mixed into JSON
  stdout.
- **FR-014**: Changing optional capability coverage MUST preserve existing true
  prerequisite checks. Missing SpecKit CLI, project initialization,
  constitution, phase command installation, or workflow-file inputs MUST still
  fail the overall prerequisite result with actionable failure messages.

### Reviewability Notes *(if applicable)*

- This spec is a narrow messaging and deterministic-coverage alignment slice.
  It intentionally excludes broad enforcement and behavior rewrites because
  those surfaces belong to TACD-002 or TACD-004.
- Historical archives, changelogs, and provenance records are not active user
  guidance and are excluded unless they are reused as current setup guidance.
- Concrete repository file references may appear in the implementation plan and
  PR packet for traceability, but active user-facing guidance should remain
  capability-first.
- Active documentation scope includes Claude prerequisite guidance
  (`speckit-pro/skills/speckit-autopilot/references/prerequisites.md`) and
  Codex prerequisite guidance
  (`speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`)
  as peer active prerequisite surfaces. They must express the same
  capability-first contract, category set, fallback/escalation boundary, and
  concrete-identifier exception policy. The scope also includes limitation,
  coach/autopilot, and adjacent autopilot entrypoint summaries only when they
  repeat current preflight or limitation wording.
- Generated payload copies are source-derived outputs. They should be
  regenerated from source when source wording changes require parity, not
  patched directly.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter
- **Projected reviewable LOC**: 190
- **Projected production files**: 1
- **Projected total files**: 8
- **Budget result**: within budget
- **Split decision**: Keep as one spec because the slice changes one
  prerequisite messaging path, focused deterministic coverage, and the active
  guidance references declared in `plan.md`. Any broader enforcement or eval
  rewrites are deferred to TACD-004.

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
  generated source-derived duplicates, or historical provenance that still
  contains concrete optional-tool names and explain why each is outside active
  guidance or source-derived.
- The review packet MUST separate repository-specific guidance from
  platform/vendor behavior; platform behavior claims require official vendor
  evidence, while repository facts should cite Racecraft source or generated
  artifacts.

## Clarifications

### Session 1 - Advisory Wording

- The prerequisite advisory reports four setup-facing capability categories:
  codebase context, library documentation, web/domain research, and source
  extraction.
- The prerequisite output uses one successful `capability_coverage` advisory
  and does not emit a per-tool available/missing inventory.
- Missing optional research or context coverage lowers confidence or requires
  fallback evidence notes; it escalates only when no acceptable evidence path
  exists or a true gate fails.
- Concrete optional tool identifiers are allowed only for platform metadata,
  exact repository file references, generated source-derived duplicates, or
  historical provenance.

### Session 2 - Active Documentation Boundary

- Active TACD-003 documentation scope is the four roadmap docs plus adjacent
  autopilot entrypoint summaries only when they repeat active preflight or
  limitation wording.
- Claude prerequisite guidance and Codex prerequisite guidance are integration
  peers. Both must express the same capability categories,
  fallback/escalation boundary, and concrete-identifier exception policy.
- Generated payload copies are source-derived and should be regenerated from
  changed sources when needed, not patched directly.
- Archives, changelogs, and fixture prose stay out of scope unless reused as
  current setup guidance or expected current behavior.
- Repository-specific guidance must cite Racecraft source or generated
  artifacts; platform/vendor behavior claims require official vendor evidence.

### Session 3 - Focused Verification Boundary

- `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh` owns focused
  `capability_coverage` JSON behavior coverage.
- TACD-003 may add narrow deterministic assertions for changed active guidance
  files only.
- The Phase 1 `generate-spec-index.sh` whitespace fix remains a checkpoint
  unblocker and is not part of the TACD-003 messaging test scope.
- Layer 3 eval expectation updates, Layer 5 pointer coverage, and broad
  named-tool enforcement remain TACD-004 scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a missing-optional-capability setup path with acceptable
  fallback coverage, prerequisite checking completes successfully and emits
  exactly one generic non-blocking `capability_coverage` advisory.
- **SC-002**: 100% of changed active Claude prerequisite, Codex prerequisite,
  limitation, coach, and autopilot guidance uses capability-first language for
  research and context support.
- **SC-003**: 0 changed active user-facing guidance passages introduce a fixed
  optional-tool installation contract or per-tool available/missing inventory,
  excluding platform metadata, exact file references, generated source-derived
  duplicates, and historical provenance.
- **SC-004**: Focused deterministic coverage verifies the changed
  `capability_coverage` JSON behavior and any changed active guidance
  assertions before implementation is considered complete.
- **SC-005**: Maintainers can review the TACD-003 PR within the declared budget
  using a traceability packet that maps every functional requirement to changed
  files and verification evidence.
- **SC-006**: Changed prerequisite output and active guidance contain no
  escalation instruction triggered solely by absent optional research or context
  capability coverage when acceptable fallback evidence exists.
- **SC-007**: Focused Layer 4 coverage proves prerequisite stdout parses as
  JSON, includes the stable top-level and check fields, and contains exactly one
  `capability_coverage` advisory without non-JSON diagnostic text on stdout.
- **SC-008**: Focused Layer 4 coverage includes at least one true prerequisite
  blocker path that still reports `all_pass=false` with an actionable failure
  message while the missing-optional-capability path remains successful.

## Assumptions

- TACD-002 has already shipped the shared capability-discovery directive for
  agent behavior, and TACD-003 only aligns prerequisite output and active
  guidance with that behavior.
- Missing optional research or context coverage can still have an acceptable
  fallback path, but the user should be told that confidence may be lower.
- User escalation happens when a task has no acceptable evidence path after
  fallback attempts or when a true prerequisite/gate fails, not merely because
  optional research or context capability coverage is absent at setup.
- Prerequisite stdout is consumed by deterministic tests and workflow callers as
  JSON; human-facing diagnostics for blockers belong in JSON fields or stderr,
  not as extra stdout prose.
- Active guidance includes prerequisite, limitation, coach, and autopilot
  messaging that users or agents rely on during current workflows.
- Historical archive, changelog, fixture-only, and provenance references are
  not active guidance unless they are reused as current setup instructions or
  expected current behavior.
- Adjacent skill entrypoint summaries are active guidance only when they repeat
  current preflight or limitation wording. Broader docs-site pages and generated
  payloads are out of scope unless source changes require regeneration.
- TACD-004 will own broader enforcement against fixed optional-tool guidance,
  including broad static checks or eval expectation changes.
