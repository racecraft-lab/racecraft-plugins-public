# Feature Specification: ART-005 - Gallery Completion - Knowledge, Reports & Editors

**Feature Branch**: `art-005-gallery-completion-knowledge-reports-editors`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Port seven planned knowledge, report, and editor gallery templates into complete standalone Racecraft artifacts, preserving the accepted one combined slice, resolving semantic export obligations from pinned upstream evidence, and delivering file:// UAT evidence."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Decks And Concepts (Priority: P1)

A reader opens the Slide Deck or Concept Explainer from the filesystem and can consume complete, representative content without needing a server, setup step, or external workflow.

**Why this priority**: These two entries are part of the planned catalog segment and must become useful standalone reading experiences before the gallery can be considered complete.

**Independent Test**: Open each artifact directly over `file://`, inspect the representative content, navigate any consumption controls, and confirm the experience is understandable without export controls unless the semantic producer/reader check proves otherwise.

**Acceptance Scenarios**:

1. **Given** the `slide-deck` catalog entry is planned and sourced from `09-slide-deck.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can step through a representative Racecraft-branded deck with accessible controls and no missing content.
2. **Given** the `concept-explainer` catalog entry is planned and sourced from `15-research-concept-explainer.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can understand the concept, worked example, and supporting content without any network-dependent behavior.

---

### User Story 2 - Inspect Status And Incident Reports (Priority: P2)

A reader opens a Status Report or Incident Report from the filesystem and can inspect a complete representative report, including status, impact, blockers, timeline, and follow-up information where appropriate.

**Why this priority**: The report entries complete the planned reporting segment and must clearly distinguish read-only reports from any upstream interaction that creates durable user-authored state.

**Independent Test**: Open each report artifact over `file://`, verify the report is complete and readable, and confirm any state-producing upstream behavior has been reconciled with the export contract before implementation proceeds.

**Acceptance Scenarios**:

1. **Given** the `status-report` catalog entry is planned and sourced from `11-status-report.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can inspect current work, in-flight work, blockers, ownership, and next milestones in a complete representative report.
2. **Given** the `incident-report` catalog entry is planned and sourced from `12-incident-report.html`, **When** a reader opens the shipped artifact over `file://`, **Then** the reader can inspect what broke, timeline, impact, response, remediation, and recurrence-prevention information in a complete representative report.

---

### User Story 3 - Export Editor Decisions As Markdown (Priority: P3)

An operator edits a Triage Board, Feature Flag configuration, or Prompt Tuner session, then copies deterministic Markdown derived from the current session state and can recover the same text manually when clipboard access fails.

**Why this priority**: The three editor entries are the only known ART-005 semantic producers and must close the required feedback loop without adding persistence, import-back, or new export kinds.

**Independent Test**: Change each editor's sample state, invoke `Copy as Markdown`, verify the copied or fallback text matches the live state, reload the page, and confirm editor working state resets while existing theme preference behavior is unchanged.

**Acceptance Scenarios**:

1. **Given** an operator has moved or edited items on the `triage-board`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic human-readable Markdown grouped by board column from the current board state.
2. **Given** an operator has changed `feature-flags`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic Markdown containing a fenced JSON block that losslessly represents the current flag state.
3. **Given** an operator has changed the `prompt-tuner`, **When** the operator chooses `Copy as Markdown`, **Then** the artifact produces deterministic Markdown containing a fenced JSON block that losslessly represents the current prompt session state.
4. **Given** clipboard access is unavailable, rejected, or throws synchronously, **When** an operator chooses `Copy as Markdown`, **Then** the artifact announces the failure as text, reveals a labeled manual-copy field containing the exact export text, and moves focus to that field.

---

### Edge Cases

- Clipboard APIs can be unavailable, rejected by the browser, or throw synchronously when opened over `file://`; the operator must still receive the exact export text.
- Reloading an editor after changes must reset editor working state to representative sample content while leaving existing theme preference behavior unchanged.
- The four currently export-free entries may prove to be semantic producers after pinned upstream inspection; implementation must stop and reconcile the contract rather than guessing from the current manifest.
- Partial delivery is invalid: an artifact file without the matching catalog status change, or a catalog status change without the artifact file, does not satisfy the feature.
- Keyboard-only users must be able to reach newly introduced horizontal scroll regions and operate all controls without losing visible focus.
- Reduced-motion users must not be required to tolerate animation, transitions, or smooth scrolling in the new artifacts.
- Color, position, and visual treatment may support meaning but must not be the only way a reader identifies status, priority, or error state.
- Missing upstream source evidence, digest evidence, or plan-time reviewability measurement blocks implementation planning from proceeding silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST port exactly these seven existing catalog entries: `slide-deck`, `concept-explainer`, `status-report`, `incident-report`, `triage-board`, `feature-flags`, and `prompt-tuner`.
- **FR-002**: The feature MUST use one immutable upstream commit, resolved during planning, as the baseline for all seven upstream source files.
- **FR-003**: Each artifact MUST preserve the core upstream content or interaction model while applying Racecraft branding, canonical embedded gallery blocks, the single-file contract, accessibility obligations, and gallery fill-region conventions.
- **FR-004**: Each shipped artifact MUST be delivered atomically with its own catalog entry status changed from `planned` to `shipped`; no other catalog value may change unless required by the resolved export classification.
- **FR-005**: The feature MUST resolve whether `slide-deck`, `concept-explainer`, `status-report`, and `incident-report` are semantic readers or semantic producers from pinned upstream interaction evidence: [NEEDS CLARIFICATION: Phase 2 must inspect the pinned upstream interaction for each currently export-free entry and confirm whether it produces durable user-authored state requiring Markdown export reconciliation, or is truly consumption-only and must retain no export control].
- **FR-006**: Any artifact confirmed as a semantic reader MUST carry no export control and MUST retain an empty export declaration.
- **FR-007**: The three known editor artifacts, `triage-board`, `feature-flags`, and `prompt-tuner`, MUST retain `markdown` as their only export kind and MUST label the export control exactly `Copy as Markdown`.
- **FR-008**: `feature-flags` and `prompt-tuner` exports MUST be deterministic Markdown documents containing lossless structured session state in fenced JSON.
- **FR-009**: `triage-board` exports MUST be deterministic, human-readable Markdown organized by board column.
- **FR-010**: Every export MUST be generated from the artifact's live state at the moment the operator invokes it.
- **FR-011**: When clipboard copy is unavailable, rejected, or throws synchronously, the artifact MUST announce the failure in text, reveal a labeled selectable manual-copy field, populate it with the exact export text, and focus it.
- **FR-012**: Editor working state MUST be memory-only and reset on reload; existing gallery theme preference behavior MUST remain unaffected.
- **FR-013**: Every new artifact MUST open directly over `file://`, remain readable with no server or install step, and avoid missing content when the network is unavailable.
- **FR-014**: New horizontal scroll regions MUST be keyboard-focusable and named; all controls MUST have visible focus and accessible names; status MUST be announced as text; reduced motion MUST be respected; color MUST never be the sole carrier of meaning.
- **FR-015**: The feature MUST preserve a tracked plain-English `file://` UAT runbook and a durable per-check result record covering all seven artifacts.
- **FR-016**: Planning MUST include a file-by-file measurement of the pinned upstream sources and declared operations before implementation starts.
- **FR-017**: If the final projection crosses a reviewability block threshold and no ratified exception exists, planning MUST stop for an operator topology decision instead of splitting automatically or inventing an exception.
- **FR-018**: The feature MUST stay within the selected single combined slice unless an explicit later operator decision changes that topology.
- **FR-019**: The feature MUST NOT add workflow-stage routing, JSON export kinds, automatic downloads, import-back, persistent editor content, shareable URL state, server storage, shared gallery foundation changes, or repairs to already-shipped templates.

### Reviewability Notes *(if applicable)*

- No ratified reviewability exception exists for this feature.
- The operator selected one combined slice after being shown that both estimates warned and suggested two slices.
- Generated templates, generated zones, process files, PR bodies, and code fences are not valid provenance for a typed reviewability exception.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (shipped gallery artifacts)
- **Secondary surfaces, if any**: N/A
- **Preset thresholds**: Warn above 400 reviewable LOC, above 6 production files, above 15 total files, or above 1 primary surface. Block above 800 reviewable LOC, above 8 production files, above 25 total files, or above 1 primary surface without a ratified exception.
- **Projected reviewable LOC**: Roadmap estimate 560 LOC; scaffold estimate 555 LOC. Both estimates warn and suggest two slices because they exceed the 400 reviewable LOC warning threshold and remain below the 800 reviewable LOC block threshold.
- **Projected production files**: 7 net-new artifact files, which exceeds the preset warning threshold of 6 production files and remains below the block threshold of 8 production files.
- **Projected total files**: Approximately 9 authored files before generated mirrors, below the total-file warning threshold of 15.
- **Budget result**: Warning accepted by operator for one combined slice; no block is established from current estimates.
- **Split decision**: The feature remains one combined ART-005 spec because the operator selected that topology. Planning must measure pinned source files and declared operations file by file; if the final projection crosses any block threshold, the workflow must stop for an operator topology decision rather than split automatically or invent an exception.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Gallery Artifact**: A standalone catalog template a reader opens from the filesystem; key attributes are identifier, title, category, representative content, interaction model, status, and export affordances.
- **Manifest Entry**: The catalog row that routes and describes an artifact; key attributes are stable id, category, title, guidance, stage, trigger, source, status, and exports.
- **Upstream Source Baseline**: The immutable upstream repository commit and seven source files used as derivative inputs; key attributes are commit identity, file path, retrieval date, and per-file digest or equivalent evidence.
- **Editor Session State**: The in-memory working data for a triage board, feature-flag configuration, or prompt tuning session; key attributes are visible values, ordering, current selections, and reset behavior.
- **Markdown Export**: The deterministic record produced from live editor state; key attributes are artifact name, generated content, stable ordering, and fenced JSON when structured state is required.
- **Manual Copy Recovery**: The fallback path used when clipboard copy fails; key attributes are visible status, labeled selectable field, exact export text, and focus movement.
- **UAT Evidence Record**: The durable acceptance record for manual `file://` checks; key attributes are artifact id, check description, verdict, environment, date, and observed result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven ART-005 catalog entries can be opened directly over `file://` and present complete representative content with no missing artifact content.
- **SC-002**: The manifest and artifact files agree for 100% of the seven entries: each shipped entry has its artifact, and no ART-005 artifact remains planned.
- **SC-003**: For all three known editors, changing visible state before `Copy as Markdown` changes the exported Markdown deterministically to match the current session state.
- **SC-004**: For all three known editors, forced clipboard unavailability, rejection, and synchronous failure each expose a labeled manual-copy field containing the same text the clipboard path would have produced.
- **SC-005**: Keyboard-only UAT covers all seven artifacts and verifies reachable named scroll regions where present, visible focus on controls, and no color-only status or priority meaning.
- **SC-006**: Reduced-motion UAT verifies that all seven artifacts remain usable without required animation, transition, or smooth-scroll behavior.
- **SC-007**: The tracked UAT result record contains a pass/fail entry for every required check across all seven artifacts, including each editor export path and manual-copy fallback path.
- **SC-008**: The plan-time reviewability record includes both warned estimates, a file-by-file pinned-source measurement, declared operations, and either a non-blocking projection or an explicit operator topology decision.

## Assumptions

- The target reader or operator opens gallery artifacts from a local filesystem and does not rely on a local server.
- Representative sample content is acceptable for all seven artifacts as long as it preserves the upstream content or interaction model and is complete enough for UAT.
- The immutable upstream commit and file digests are resolved during planning rather than guessed in the specification.
- The existing gallery theme preference behavior remains owned by the shared canonical block and is not redesigned by ART-005.
- Functional fidelity means preserving the recognizable content model and interaction purpose of each upstream file, not pixel-perfect upstream styling.
- Generated payload copies and installed-cache proofs are handled by authoritative repository tooling after source changes; this specification does not authorize hand-editing generated mirrors.
