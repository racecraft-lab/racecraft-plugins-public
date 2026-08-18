# Feature Specification: ART-004 Gallery Completion - Design & Prototyping

**Feature Branch**: `art-004-gallery-completion-design-prototyping`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Complete the gallery's six planned design and prototyping artifacts, repair the known horizontal-scroll keyboard access defect, absorb ART-020, and keep the combined slice reviewable under the speckit-pro-reviewability preset."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keyboard-scroll wide regions (Priority: P1)

A keyboard-only reader can reach, identify, and horizontally scroll every wide region in the shipped gallery, including the five existing affected regions and any new wide regions introduced by the six design and prototyping artifacts.

**Why this priority**: The current gallery already ships unreachable horizontal regions for keyboard-only Safari readers, and completing more artifacts must not widen that accessibility defect.

**Independent Test**: Can be tested by opening the affected gallery artifacts, navigating by keyboard only, confirming each wide region receives focus in sequence, and using keyboard scrolling without relying on pointer input.

**Acceptance Scenarios**:

1. **Given** a keyboard-only reader opens `code-approaches`, `implementation-plan`, or `module-map`, **When** they tab through the page, **Then** each affected horizontal region receives focus in reading order and exposes a meaningful accessible name.
2. **Given** a keyboard-only reader focuses any horizontal overflow region in the six new artifacts, **When** they use keyboard scroll controls supported by the browser, **Then** the hidden horizontal content becomes reachable without pointer input.
3. **Given** the gallery guard evaluates an artifact containing an unnamed or unfocusable horizontal overflow region, **When** the guard runs, **Then** the defect is reported rather than allowed to ship.

---

### User Story 2 - Open complete design artifacts offline (Priority: P2)

A reader can open each of the six new design and prototyping files directly from the local file system and inspect every distinct section and interaction carried by the pinned upstream template while remaining offline.

**Why this priority**: The gallery catalog already promises these six shipped examples; readers need the actual files to inspect visual directions, a design system, component states, motion timing, a clickable flow, and an SVG illustration.

**Independent Test**: Can be tested by opening each new artifact directly while offline, comparing its visible sections and interactions against the pinned source inventory, and confirming the artifact remains branded and readable.

**Acceptance Scenarios**:

1. **Given** a reader opens `visual-designs`, `design-system`, `component-variants`, `animation-prototype`, `interaction-prototype`, or `svg-illustrations` directly from the local file system, **When** the page loads offline, **Then** the artifact is readable, branded, and usable without any build step or sibling resource.
2. **Given** an upstream template contains a distinct section, state, motion timing, decision surface, or interaction, **When** the corresponding gallery artifact is reviewed, **Then** that behavior or decision surface is preserved even if repeated sample data is compacted.
3. **Given** the catalog entry for any of the six ports is inspected after completion, **When** its row is compared with the pre-existing catalog record, **Then** only its status has changed from planned to shipped.

---

### User Story 3 - Export a selected design decision (Priority: P3)

A reader chooses one visual direction or one base component variant, records a rationale, and copies that live decision as either an actionable prompt or Markdown, with a selectable fallback if clipboard access is refused.

**Why this priority**: Two of the promised artifacts declare export behavior; the durable value is the reader's conclusion and rationale, not a static page alone.

**Independent Test**: Can be tested by selecting each exportable artifact's decision, entering a rationale, using both copy controls, and denying clipboard access to verify the fallback payload remains selectable.

**Acceptance Scenarios**:

1. **Given** a reader selects one visual direction and enters a rationale, **When** they choose `Copy as prompt` or `Copy as Markdown`, **Then** the copied payload names the chosen direction, includes the rationale, and provides enough context to act without reopening the artifact.
2. **Given** a reader selects one base component variant and enters a rationale, **When** they choose `Copy as prompt` or `Copy as Markdown`, **Then** the copied payload names the chosen variant, includes the rationale, and preserves the relevant component-state context.
3. **Given** clipboard access is refused, **When** the reader uses either export control, **Then** the page announces the refusal in text and reveals a selectable fallback containing the same live payload.

### Edge Cases

- A reader blocks clipboard access or uses a browser that does not permit local-file clipboard writes.
- A reader leaves the rationale blank before using an export control.
- Optional typeface substitution occurs because the preferred typeface is not available offline.
- A pinned upstream template contains repeated examples that can be compacted without losing a distinct section, state, motion, or interaction.
- A horizontal overflow region is visually subtle, nested inside a larger section, or introduced by a new port rather than one of the five known affected shipped regions.
- The plan-time reviewability gate blocks the chosen combined slice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The gallery MUST ship one directly openable local artifact for each planned design and prototyping entry: `visual-designs`, `design-system`, `component-variants`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- **FR-002**: Each new artifact MUST work fully offline when opened directly from the local file system, with no build step, bundled runtime, sibling asset, or external dependency except optional typeface substitution.
- **FR-003**: Each new artifact MUST preserve every distinct section, state, motion, decision surface, and interaction from its pinned upstream source while allowing repeated sample data to be compacted.
- **FR-004**: All six upstream sources MUST be pinned to `anthropics/html-effectiveness` commit `58c305be97f47b26b678f2c07dec01d4242268ec` and carry the exact five-label attribution header with the matching source filename recorded in `manifest.json`.
- **FR-005**: Each new artifact MUST embed the canonical `BRAND-KIT` and `GALLERY-HEAD` regions with their markers byte for byte.
- **FR-006**: Each new port MUST change exactly one existing catalog value, its status from planned to shipped; identifiers, categories, stages, triggers, source metadata, when-to-use text, signal vocabulary, and export declarations MUST remain stable.
- **FR-007**: `visual-designs` MUST allow exactly one selected visual direction plus a reader-provided rationale and MUST expose visible controls labeled `Copy as prompt` and `Copy as Markdown`.
- **FR-008**: `component-variants` MUST show all required component states, allow exactly one selected base variant plus a reader-provided rationale, and expose visible controls labeled `Copy as prompt` and `Copy as Markdown`.
- **FR-009**: `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` MUST remain read-only and MUST NOT expose prompt, Markdown, or other export affordances.
- **FR-010**: Prompt and Markdown exports MUST derive from the live reader state, name the conclusion and rationale, include enough context to act without reopening the page, announce copy results in text, and reveal a selectable fallback when clipboard access is refused.
- **FR-011**: Every horizontal overflow region in shipped and newly completed artifacts MUST be sequentially focusable and have a specific meaningful accessible name.
- **FR-012**: The five existing affected horizontal scroll containers in `code-approaches`, `implementation-plan`, and `module-map` MUST receive the same keyboard focus and accessible-name repair required for new wide regions.
- **FR-013**: The gallery verification guard MUST include a global assertion and a negative fixture that prevent unnamed or unfocusable horizontal overflow regions from shipping, without naming the test after ART-004 or ART-020.
- **FR-014**: ART-004 MUST absorb ART-020 completely, mark ART-020 as superseded, keep one combined slice through specification, and stop for a human-approved split if the plan-time reviewability gate blocks the combined scope.

### Reviewability Notes *(if applicable)*

- The combined scope is intentional because the fixed design-concept answer selected one combined slice after weighing the advisory reviewability warning.
- The advisory setup estimate was 865 projected reviewable LOC across twelve authored files or surfaces, fourteen functional requirements, and seven capability groups, with a warning and a suggested three-slice topology.
- The advisory estimate is not plan evidence. The authoritative plan-time reviewability gate must measure actual declared file operations before task generation.
- If the authoritative gate blocks the combined slice, the feature stops for a human-approved split. Fidelity must not be reduced, and ART-020 must not be removed from ART-004 as a workaround.
- Typed reviewability exceptions are rare operator-owned overrides. Accepted classes are refactor, infra, and upgrade, but generated templates, generated zones, `.process` files, PR bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: UI gallery artifacts
- **Secondary surfaces, if any**: harness/adapter verification, seed/config catalog metadata, docs/process roadmap disposition, generated release artifacts
- **Projected reviewable LOC**: 865 advisory net-new LOC before plan evidence; excludes generated payloads, installed-cache proofs, generated reference pages, vendored upstream originals, and lockfiles
- **Projected production files**: 9 authored surfaces: six gallery artifacts, three existing gallery artifact repairs
- **Projected total files**: 12 authored files or surfaces before generated release artifacts
- **Budget result**: warning accepted pending authoritative plan gate
- **Split decision**: Remains one ART-004 spec because the recorded user answer selected one combined slice; if Plan blocks this shape, stop for a human-approved split while preserving full functional fidelity and keeping ART-020 absorbed.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
- Review order MUST separate the ART-020 accessibility repair and guard, the six gallery ports, catalog status flips, generated release artifacts, and PR review packet evidence.
- Verification evidence MUST include the repository suite result, the global horizontal-scroll guard result, direct local-file/offline artifact checks, export success and clipboard-refusal checks for the two decision artifacts, generated-artifact regeneration evidence, and the plan-time reviewability gate result.
- Known gaps MUST explicitly state whether the combined slice passed the authoritative reviewability gate; if it did not pass, the PR must not proceed without the human-approved split.

### Key Entities *(include if feature involves data)*

- **Gallery Artifact**: A cataloged offline example page identified by a stable gallery identifier, status, category, stage, source metadata, usage text, and export declaration.
- **Pinned Upstream Source**: The source template file and commit used as the reproducibility baseline for each port.
- **Horizontal Overflow Region**: A wide content region that can hide content horizontally and therefore needs sequential keyboard focus plus a meaningful accessible name.
- **Design Decision Export**: The live conclusion and rationale payload produced by `visual-designs` or `component-variants` as either prompt text or Markdown.
- **Reviewability Budget**: The declared scope, projected review surface, and split decision used to decide whether the combined slice may advance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All six planned design and prototyping catalog entries can be opened directly from the local file system while offline and inspected without missing a distinct upstream section or interaction.
- **SC-002**: Keyboard-only review reaches and horizontally scrolls 100% of wide regions in the five existing affected containers and in every new artifact.
- **SC-003**: 100% of horizontal overflow regions in shipped gallery artifacts have a meaningful accessible name and are covered by a guard that fails on an unnamed or unfocusable negative fixture.
- **SC-004**: For both exportable artifacts, a reader can complete selection, rationale entry, prompt copy, Markdown copy, and clipboard-refusal fallback checks in under 3 minutes per artifact.
- **SC-005**: Catalog review confirms exactly six status changes from planned to shipped and zero unintended changes to identifiers, categories, stages, triggers, source metadata, when-to-use text, signal vocabulary, or export declarations.
- **SC-006**: Release review finds regenerated payloads, proofs, and generated reference artifacts aligned with the authored source changes, with no hand-edited generated mirrors.
- **SC-007**: Plan evidence either clears the authoritative reviewability gate for one combined slice or records a stop before task generation for a human-approved split.

## Assumptions

- The six gallery entries and the three existing affected shipped artifacts already exist in the catalog and can be updated without changing their identifiers or meaning.
- The pinned upstream source files remain accessible for planning and implementation evidence, but the upstream originals are not committed as gallery artifacts.
- Optional typeface substitution is acceptable when a reader is offline, provided the artifacts remain readable and usable.
- Empty rationale handling can guide the reader to provide a rationale before export rather than inventing rationale text.
- Generated release artifacts are derived from authoritative source after authored changes and are excluded from reviewability LOC accounting.
- No vertical-scroll or unrelated accessibility remediation is part of this feature.
