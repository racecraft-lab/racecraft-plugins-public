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
- A stale enhanced selector state, unavailable selector metadata, or unsupported platform/scope combination is encountered; the page explains the unsupported or ambiguous state in text, keeps supported static path guidance available, and routes users to safe install or troubleshooting handoffs without claiming a local diagnostic was run.
- Repository metadata is temporarily unavailable during content generation; the page falls back to explicit unavailable-state content rather than stale generated output.
- Source and generated payload versions differ; the checker reports mismatch and routes users to lightweight troubleshooting handoffs without attempting repair.
- A user opens the page without browser scripting; all selector paths, checker comparison values, diagram nodes, and checklist items remain accessible as static content.
- A user tries to infer that the browser can run commands; the page labels commands as copyable guidance only and never presents them as executable browser actions.
- Existing DOC-008 troubleshooting ownership is not ready; mismatch handoffs remain lightweight and avoid replacing the future full troubleshooting matrix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The primary DOC-006 user-facing surface MUST be the existing choose-your-path docs route, not a separate docs route.
- **FR-002**: The page MUST provide a platform and path selector for Claude Code and Codex guidance.
- **FR-003**: The selector MUST include install-scope choices where a selected platform path supports more than one scope, and it MUST provide an explicit text state for unsupported, unavailable, or ambiguous platform/scope combinations while keeping supported static path guidance available.
- **FR-004**: Each selected path MUST display copyable command blocks with visible platform labels, install-scope labels, prerequisite notes, platform-specific expected success signals, and next documentation links.
- **FR-005**: The selected path guidance MUST keep Claude Code and Codex command records separate, so selected Claude guidance cannot render Codex skill invocations and selected Codex guidance cannot render Claude Code marketplace command guidance.
- **FR-006**: Codex guidance MUST describe Codex skill invocation as Codex `$skill` usage, not as Claude slash-command usage.
- **FR-007**: Manifest-backed selector and checker values MUST be read from checked-in repository JSON or manifest sources during docs content generation. Command templates, prerequisites, success signals, and handoff labels that are not present in those JSON or manifest files MAY be maintained as a small checked-in docs metadata source, but MUST use JSON-derived values for manifest-backed fields and MUST be covered by focused metadata/rendering validation.
- **FR-008**: The feature MUST NOT parse install Markdown as a machine data source and MUST NOT require or commit a persistent generated metadata file for selector or checker facts.
- **FR-009**: The page MUST include a repository-only manifest and version checker that compares source repository marketplace or plugin values against generated payload marketplace or manifest values from `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/claude/speckit-pro/.claude-plugin/plugin.json`, and `dist/codex/speckit-pro/.codex-plugin/plugin.json`.
- **FR-010**: The checker MUST explain the expected consistency rule for each compared value and show the values being compared. Equality checks MUST be limited to stable repository consistency fields such as plugin name, version, marketplace source/path, and source/dist counterpart presence; intentional platform packaging differences MUST be displayed as informational context rather than false mismatches.
- **FR-011**: The checker MUST NOT accept pasted user JSON, inspect local user configuration, or diagnose user machine state.
- **FR-012**: The page MUST include an accessible generated-payload diagram that distinguishes source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache as separate nodes.
- **FR-013**: The page MUST include a compact first-run checklist with checkpoints for platform install route, Spec Kit CLI exists/version, constitution, roadmap or SPEC-ID selection, GitHub CLI, `jq`, branch or worktree and clean-state review, scaffold output artifacts, and docs validation evidence.
- **FR-014**: All selector, checker, diagram, and checklist aids MUST be keyboard usable through native controls where possible and backed by semantic static fallback tables or equivalent static content.
- **FR-015**: Browser behavior MUST NOT run shell commands, read local user files, write configuration, install plugins, or invoke local plugin workflows.
- **FR-016**: Mismatch, unavailable, or caution states MUST provide lightweight troubleshooting handoffs to existing content or DOC-008-owned troubleshooting content without expanding into a full troubleshooting matrix.
- **FR-017**: The feature MUST include focused validation for source-derived metadata and rendering behavior in addition to standard docs validation and link validation, including at least one passing metadata state, one mismatch metadata state, one unavailable metadata state, command-surface leakage checks, no pasted-JSON/local-diagnostic UI, handoff links, first-run checkpoint coverage, and required-field coverage for every selector path.

### Clarifications

- **Command metadata source boundary**: For DOC-006, "source-derived" means manifest-backed values already present in checked-in marketplace or plugin JSON are read during docs content generation and interpolated into selector/checker output. Command sequences, prerequisites, success signals, and handoff labels that are not represented in those JSON manifests may live in a small checked-in docs metadata helper as curated documentation source, provided the helper uses or cross-checks JSON-derived variables for manifest-backed values, references the authoritative install handoff pages, and is covered by the focused metadata/rendering fixture. DOC-006 MUST NOT parse install Markdown as a data source and MUST NOT commit generated selector/checker metadata output.
- **Metadata checker inputs**: The repository-only checker compares the six checked-in marketplace and plugin manifest files named in FR-009. It must never read installed cache files, user home-directory files, pasted JSON, or browser-local configuration.
- **Checker comparison rules**: The checker equality-compares stable repository consistency fields such as plugin name, version, marketplace source/path, and source/dist counterpart presence. Fields that intentionally differ between source and distribution packaging, such as Codex `skills` path rewrites or platform-specific descriptions, should be shown as informational context with an explicit explanation instead of failing the checker.
- **Mismatch and unavailable handoffs**: Mismatch, unavailable, and caution states should show the relevant repository consistency rule, the compared or unavailable values, and lightweight links for installers to platform install stale-update checkpoints or troubleshooting shell content, plus maintainer links to reference or contribute/release content. They must not become a symptom matrix, cache diagnosis, update procedure, rollback guide, or security/trust model.
- **First-run checklist scope**: DOC-006 includes compact safe checkpoints for platform install route, Spec Kit CLI exists/version, constitution, roadmap or SPEC-ID, `gh`, `jq`, branch/worktree and clean-state review, scaffold output artifacts, and docs validation evidence. It should not mirror the full first-run tutorial or absorb DOC-008 troubleshooting/deeper failure diagnosis or DOC-010 broad accessibility, responsive, deep-link, and docs-CI hardening.
- **Platform command boundaries**: Claude Code path records may show Claude Code marketplace and plugin commands such as `/plugin`, `/reload-plugins`, and `/speckit-pro:<skill>`. Codex path records may show Codex app or CLI guidance such as `codex`, `/plugins`, `@SpecKit Pro` install actions, `$install`, and `$speckit-*`. A selected path must not mix the other platform's selected command sequence into its copyable guidance.
- **Unsupported and ambiguous selector states**: Supported platform/scope combinations are limited to the checked-in selector path records. If progressive enhancement encounters no selected path, more than one matching path, an unsupported platform/scope pair, or unavailable selector metadata, the page must identify that state in text, keep the complete static supported-path content reachable, and point to safe install or DOC-008-owned troubleshooting handoffs. This state must not claim to inspect local files, run a diagnostic, write configuration, or repair the user's environment.
- **Expected success signals**: Claude Code command blocks should identify observable success signals such as marketplace added, plugin installed or reloaded, plugin visible in `/plugin`, and `/speckit-pro:speckit-status` responding where relevant. Codex command blocks should identify observable success signals such as marketplace/plugin visible, install skill report with copied TOML filenames or restart instruction, expected TOML destination contents, and a new thread loading `$speckit-*` skills.
- **Static-first component shape**: DOC-006 may preserve the `choose-your-path` route by converting the content file to MDX and importing one small Astro component, provided the component renders complete static HTML and uses only minimal progressive enhancement for filtering or selection.
- **Keyboard behavior**: Selector and checker controls should use native form or button behavior where possible. Tab and Shift+Tab must reach controls in reading order, Space or Enter must activate controls, focus must remain visible, and selected state must be visually distinct from focus. If a custom control is used instead of a native form control, its accessible name, role, and selected, current, or expanded state must be programmatically exposed to assistive technologies; visual-only selected state is insufficient.
- **Semantic fallback content**: The selector fallback must visibly include every supported path with platform, scope, prerequisites, command label or sequence, success signal, and next link. Checker and diagram fallback tables or lists must include the same facts as any enhanced view; a `noscript`-only fallback is insufficient.
- **Copy affordance boundary**: Copy buttons are optional progressive enhancement. If included, commands must remain visible/selectable in normal code blocks, copy controls must be native buttons, clipboard failure must have visible status, and raw commands must never be hidden behind JavaScript.
- **Accessible payload diagram**: The generated-payload diagram should be a text-backed flow where source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache are real headings, list items, or table rows. Visual connectors may be decorative, but no information may depend on hover, drag, zoom, click, or pointer-only interaction.

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

- **Selector Path**: A supported platform and install-scope choice with labels, prerequisites, commands, success signals, next docs links, and a platform discriminator that prevents Claude/Codex command leakage.
- **Command Guidance**: A copyable command sequence with platform boundary metadata, curated command text, JSON-derived manifest-backed values where applicable, and expected user-visible outcome.
- **Manifest Consistency Check**: A repository-scoped comparison between checked-in source values and generated payload values from the six declared marketplace and plugin manifest files, including match or mismatch state.
- **Generated Payload Diagram Node**: A labeled static diagram node representing source tree, Claude distribution, Codex distribution, marketplace entries, or Codex cache.
- **First-Run Checkpoint**: A safe readiness item users can review before running local commands.
- **Troubleshooting Handoff**: A lightweight link or message that points users from mismatch or caution states to existing or DOC-008-owned troubleshooting material.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time installer can identify the correct platform and install-scope path and locate the relevant command sequence within 60 seconds.
- **SC-002**: 100% of supported selector paths display platform label, install-scope label where applicable, prerequisites, copyable commands, platform-specific expected success signal, and next docs link.
- **SC-003**: 100% of repository metadata comparisons show both compared values, a pass or mismatch state, and the expected consistency rule.
- **SC-004**: The page remains usable with browser scripting disabled, including selector fallback content, checker comparison content, payload diagram content, and first-run checklist content.
- **SC-005**: Keyboard-only users can reach and operate all interactive aids without losing context or encountering hidden required information.
- **SC-006**: Focused validation detects at least one passing metadata/rendering fixture, at least one mismatch metadata/rendering fixture, no selected-path leakage between Claude Code and Codex command surfaces, an unsupported or ambiguous selector-state fixture, and required fields for every selector path.
- **SC-007**: Standard docs validation and link validation pass for the choose-your-path page and its handoff links.

## Assumptions

- The existing choose-your-path page is the correct first-viewport destination for install-path decision support.
- Existing Claude Code, Codex, first-run, lifecycle, and generated payload docs remain the authoritative detailed handoff pages.
- Checked-in source marketplace and plugin manifest files are available during docs content generation.
- Generated payload marketplace and manifest files exist in the repository when the checker compares distribution metadata.
- JSON and manifest files provide names, versions, paths, and consistency values, but they do not provide every command sequence, prerequisite, or success signal needed by the docs selector.
- Selector and checker aids can use progressive enhancement, but the complete facts must also be present as semantic static content.
- DOC-008 will own full troubleshooting, security and trust model, update, rollback, and cache-diagnosis content.
