# Feature Specification: Safe Interactive Selector and Validation Aids

**Feature Branch**: `doc-006-safe-interactive-selector-and-validation-aids`

**Created**: 2026-06-16

**Status**: Draft

**Input**: User description: "Enhance the existing choose-your-path docs route with static-first selector and checker aids that derive their facts from checked-in repository metadata at build time, without executing local plugin workflows from the browser."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the correct install path (Priority: P1)

As a new or returning installer, I can select my platform and supported install scope on the choose-your-path page and see only the commands, prerequisites, expected success signals, and next docs links that apply to that path.

**Why this priority**: This is the core user value. Users must be able to choose the right path without mixing Claude Code, Codex, repository-scoped, personal marketplace, or generated payload guidance.

**Independent Test**: Can be tested by reviewing each selector choice and confirming that the visible command sequence, labels, prerequisites, success signals, and handoff links match the selected platform and scope while unrelated path content stays hidden or clearly inactive.

**Acceptance Scenarios**:

1. **Given** a user has not made a selector choice, **When** they view the choose-your-path page, **Then** they see a static fallback summary of all supported platform and scope paths.
2. **Given** a user selects a Claude Code path, **When** the guidance is displayed, **Then** the command sequence and copyable blocks use Claude Code labels and do not present Codex skill invocation as Claude slash-command usage.
3. **Given** a user selects a Codex path, **When** the guidance is displayed, **Then** the command sequence and copyable blocks use Codex labels and do not include Claude Code marketplace command guidance as the selected path.
4. **Given** a path supports multiple install scopes, **When** the user changes scope, **Then** the visible prerequisites, commands, success signal, and next docs links update to the selected scope only.

---

### User Story 2 - Inspect repository metadata consistency (Priority: P2)

As a maintainer or evaluator, I can inspect a repository-only manifest and version checker that compares checked-in marketplace and plugin manifest values and explains which values must stay in sync.

**Why this priority**: Repository consistency is a visible trust signal for install documentation and generated payload guidance, but it must stay read-only and repository-scoped.

**Independent Test**: Can be tested by changing fixture metadata inputs in a focused rendering or metadata fixture and confirming that the checker reports matching and mismatching states with clear labels and handoff guidance.

**Acceptance Scenarios**:

1. **Given** checked-in source and generated payload metadata values match, **When** the checker renders, **Then** users see a clear passing consistency state and the values compared.
2. **Given** checked-in source and generated payload metadata values differ in a fixture, **When** the checker renders, **Then** users see the mismatched values, the expected consistency rule, and a lightweight troubleshooting handoff.
3. **Given** a user wants to verify their own local configuration, **When** they view the checker, **Then** the page explains that the checker is repository-scoped and does not accept pasted user JSON or inspect local user files.

---

### User Story 3 - Review safe first-run checkpoints (Priority: P3)

As a cautious first-run user, I can review a generated payload diagram and first-run checklist with static fallback content so I understand the expected checkpoints before running local workflows myself.

**Why this priority**: The page should help users understand payload flow and readiness checks while keeping browser behavior safe and non-executing.

**Independent Test**: Can be tested by disabling browser scripting or using keyboard-only navigation and confirming that the diagram, checklist, and handoff content remain readable, reachable, and complete.

**Acceptance Scenarios**:

1. **Given** browser scripting is unavailable or disabled, **When** the user opens the page, **Then** the generated payload diagram and first-run checklist remain available as semantic static content.
2. **Given** the user navigates with a keyboard, **When** they move through selector, checker, diagram, and checklist controls, **Then** focus order, labels, and selected states are understandable without pointer input.
3. **Given** the user reviews first-run readiness, **When** they inspect the checklist, **Then** it includes checkpoints for Spec Kit CLI, constitution, GitHub CLI, `jq`, branch or worktree state, platform install route, scaffold output, and docs validation.

### Edge Cases

- A platform path has no additional install scope choices; the selector still presents a complete path without implying unsupported scopes.
- Repository metadata is temporarily unavailable during content generation; the page falls back to explicit unavailable-state content rather than stale generated output.
- Source and generated payload versions differ; the checker reports mismatch and routes users to lightweight troubleshooting handoffs without attempting repair.
- A user opens the page without browser scripting; all selector paths, checker comparison values, diagram nodes, and checklist items remain accessible as static content.
- A user tries to infer that the browser can run commands; the page labels commands as copyable guidance only and never presents them as executable browser actions.
- Existing DOC-008 troubleshooting ownership is not ready; mismatch handoffs remain lightweight and avoid replacing the future full troubleshooting matrix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The primary DOC-006 user-facing surface MUST be the existing choose-your-path docs route, not a separate docs route.
- **FR-002**: The page MUST provide a platform and path selector for Claude Code and Codex guidance.
- **FR-003**: The selector MUST include install-scope choices where a selected platform path supports more than one scope.
- **FR-004**: Each selected path MUST display copyable command blocks with visible platform labels, install-scope labels, prerequisite notes, expected success signals, and next documentation links.
- **FR-005**: The selected path guidance MUST keep Claude Code command guidance separate from Codex command guidance.
- **FR-006**: Codex guidance MUST describe Codex skill invocation as Codex skill usage, not as Claude slash-command usage.
- **FR-007**: Command and checker facts MUST be derived from checked-in repository JSON or manifest sources during docs content generation.
- **FR-008**: The feature MUST NOT require or commit a persistent generated metadata file for selector or checker facts.
- **FR-009**: The page MUST include a repository-only manifest and version checker that compares source repository marketplace or plugin values against generated payload marketplace or manifest values.
- **FR-010**: The checker MUST explain the expected consistency rule for each compared value and show the values being compared.
- **FR-011**: The checker MUST NOT accept pasted user JSON, inspect local user configuration, or diagnose user machine state.
- **FR-012**: The page MUST include an accessible generated-payload diagram that distinguishes source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache as separate nodes.
- **FR-013**: The page MUST include a first-run checklist with checkpoints for Spec Kit CLI, constitution, GitHub CLI, `jq`, branch or worktree state, platform install route, scaffold output, and docs validation.
- **FR-014**: All selector, checker, diagram, and checklist aids MUST be keyboard usable and backed by semantic static fallback tables or equivalent static content.
- **FR-015**: Browser behavior MUST NOT run shell commands, read local user files, write configuration, install plugins, or invoke local plugin workflows.
- **FR-016**: Mismatch, unavailable, or caution states MUST provide lightweight troubleshooting handoffs to existing content or DOC-008-owned troubleshooting content without expanding into a full troubleshooting matrix.
- **FR-017**: The feature MUST include focused validation for source-derived metadata and rendering behavior in addition to standard docs validation and link validation.

### Reviewability Notes *(if applicable)*

- Static docs content, focused metadata fixtures, generated zones, and `.process` workflow records are not reviewability exceptions.
- Any future generated output must be declared separately and excluded from production reviewable LOC only when the generator and provenance are visible.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: seed/config, harness/adapter
- **Projected reviewable LOC**: 450-700 excluding generated or fixture-only artifacts
- **Projected production files**: 3-6
- **Projected total files**: 5-9
- **Budget result**: within budget
- **Split decision**: This remains one spec because the selector, repository metadata checker, payload diagram, checklist, and focused validation all support one docs page outcome. Full troubleshooting, update, rollback, cache diagnosis, and command reference expansion remain out of scope and belong to later specs.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Selector Path**: A supported platform and install-scope choice with labels, prerequisites, commands, success signals, and next docs links.
- **Command Guidance**: A copyable command sequence with platform boundary metadata and expected user-visible outcome.
- **Manifest Consistency Check**: A repository-scoped comparison between checked-in source values and generated payload values, including match or mismatch state.
- **Generated Payload Diagram Node**: A labeled static diagram node representing source tree, Claude distribution, Codex distribution, marketplace entries, or Codex cache.
- **First-Run Checkpoint**: A safe readiness item users can review before running local commands.
- **Troubleshooting Handoff**: A lightweight link or message that points users from mismatch or caution states to existing or DOC-008-owned troubleshooting material.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time installer can identify the correct platform and install-scope path and locate the relevant command sequence within 60 seconds.
- **SC-002**: 100% of supported selector paths display platform label, install-scope label where applicable, prerequisites, copyable commands, expected success signal, and next docs link.
- **SC-003**: 100% of repository metadata comparisons show both compared values, a pass or mismatch state, and the expected consistency rule.
- **SC-004**: The page remains usable with browser scripting disabled, including selector fallback content, checker comparison content, payload diagram content, and first-run checklist content.
- **SC-005**: Keyboard-only users can reach and operate all interactive aids without losing context or encountering hidden required information.
- **SC-006**: Focused validation detects at least one passing metadata/rendering fixture and at least one mismatch metadata/rendering fixture.
- **SC-007**: Standard docs validation and link validation pass for the choose-your-path page and its handoff links.

## Assumptions

- The existing choose-your-path page is the correct first-viewport destination for install-path decision support.
- Existing Claude Code, Codex, first-run, lifecycle, and generated payload docs remain the authoritative detailed handoff pages.
- Checked-in source marketplace and plugin manifest files are available during docs content generation.
- Generated payload marketplace and manifest files exist in the repository when the checker compares distribution metadata.
- Selector and checker aids can use progressive enhancement, but the complete facts must also be present as semantic static content.
- DOC-008 will own full troubleshooting, security and trust model, update, rollback, and cache-diagnosis content.
