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

**Per-port fidelity evidence**:

| Artifact | Observable acceptance evidence |
|---|---|
| `visual-designs` | Four directions remain visible; the light/dark background choice updates every stage; exports use the selected direction and rationale. |
| `design-system` | Color, typography, spacing, shape, and components sections render offline; every wide region is keyboard-scrollable and named. |
| `component-variants` | Padding value, border selection, shadow state, all variant states, reset-to-default behavior, the live snippet, and selected base-variant/rationale exports remain operable. |
| `animation-prototype` | The task completes through its staged sequence, the second task activation visibly resets the row, and easing controls update the active choice and timing. |
| `interaction-prototype` | Dragging exposes the insertion indicator, reorders the DOM, removes transient dragging state at completion, and provides a visible path back to the initial retained order. |
| `svg-illustrations` | Queue, retry, and fan-out illustrations plus palette rules render inline without external assets; upstream download controls are omitted because this catalog row declares no exports. |

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
- A reader invokes an export without choosing a direction/base variant, without entering a rationale, or with whitespace-only rationale text.
- A reader leaves the rationale blank before using an export control.
- Optional typeface substitution occurs because the preferred typeface is not available offline.
- A pinned upstream template contains repeated examples that can be compacted without losing a distinct section, state, motion, or interaction.
- A horizontal overflow region is visually subtle, nested inside a larger section, or introduced by a new port rather than one of the five known affected shipped regions.
- Safari keyboard navigation requires browser or system settings that make all
  webpage controls reachable by sequential keyboard navigation.
- A reader enables reduced motion while reviewing animation timing, drag or
  linked-screen transitions, background/theme transitions, or horizontal scroll
  behavior.
- The plan-time reviewability gate blocks the chosen combined slice.

## Clarifications

### Session 1 - Source structure and fill regions

- The exact fill-region/source inventory in the Functional Fidelity Inventory is
  authoritative for the six ports.
- Only repeated sample data may be compacted. Every distinct section, state,
  easing choice, interaction note, open question, and illustration concept is
  retained.
- New list slots are limited to `visual-designs.directions`,
  `component-variants.variants`, and `interaction-prototype.views`.
- Load-bearing selectors are preserved or intentionally translated with
  behaviorally equivalent selectors; styling-only classes are not frozen.
- Functional fidelity is demonstrated by the per-port observable acceptance
  evidence above, not by comparing source line counts.

### Session 2 - Decision exports

- Prompt and Markdown exports share one ordered plain-line payload; only their
  artifact-specific lead sentence differs.
- Each decision uses a keyboard-persistent radio group and reads the checked
  choice, visible label/note, rationale, and relevant live controls at the time
  the copy button is invoked.
- A complete decision requires one choice and a non-whitespace rationale.
  Invalid attempts do not call the clipboard or reveal a fallback.
- Accessible status messages identify the missing input, focus the first
  missing control, and set `aria-invalid` only on a blank rationale field.
- Clipboard refusal reveals and focuses the exact payload in a selectable
  textarea. An invocation counter prevents an older pending copy result from
  overwriting newer status or fallback state.

### Session 3 - Global keyboard-scroll guard

- Every intentional horizontal scroll container self-identifies in markup with
  `data-rc-keyboard-scroll="horizontal"`; the guard does not infer layout by
  parsing CSS selectors.
- Every declared scroll container uses `tabindex="0"`, `role="group"`, and a
  specific non-empty `aria-label`.
- The RED proof is one synthetic gallery artifact whose declared scroll region
  has its role and label but omits `tabindex`; the durable test name describes
  keyboard-scroll behavior and contains no temporary spec ID.
- Manual UAT reuses ART-003's real `file://`, CDP, focus, arrow-key, and
  scroll-position procedure while writing separate ART-004 results.
- The guard sweeps every manifest-shipped artifact and separately proves that
  the six new IDs plus `code-approaches`, `implementation-plan`, and
  `module-map` are included after the six status flips.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The gallery MUST ship one directly openable local artifact for each planned design and prototyping entry: `visual-designs`, `design-system`, `component-variants`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- **FR-002**: Each new artifact MUST work fully offline when opened directly from the local file system, with no build step, bundled runtime, sibling asset, or external dependency except optional typeface substitution. If the preferred typeface is unavailable or its remote request fails, the artifact MUST fall through to the canonical brand-kit system or generic font stacks, keep visible text and controls readable, and avoid making any icon font or private-use glyph the only carrier of control, status, or artifact meaning.
- **FR-003**: Each new artifact MUST preserve every distinct section, state, motion, decision surface, and interaction from its pinned upstream source while allowing only the repeated sample groups named in the Functional Fidelity Inventory to be compacted. For read-only artifacts, this preservation is constrained by FR-009: upstream export, copy, or download controls are not retained as active, disabled, or placeholder controls when the manifest declares `exports: []`; the informational content they expose MUST remain discoverable in-page.
- **FR-004**: All six upstream sources MUST be pinned to `anthropics/html-effectiveness` commit `58c305be97f47b26b678f2c07dec01d4242268ec` and carry the exact five-label attribution header with the matching source filename recorded in `manifest.json`.
- **FR-005**: Each new artifact MUST embed the canonical `BRAND-KIT` and `GALLERY-HEAD` regions with their markers byte for byte.
- **FR-006**: Each new port MUST change exactly one existing catalog value, its status from planned to shipped; identifiers, categories, stages, triggers, source metadata, when-to-use text, signal vocabulary, and export declarations MUST remain stable. Manifest validation MUST treat any missing row, extra row, non-status field mutation, or wrong status-flip count as blocking drift.
- **FR-007**: `visual-designs` MUST allow exactly one keyboard-persistent selected visual direction plus a required reader-provided rationale and MUST expose visible controls labeled `Copy as prompt` and `Copy as Markdown`; its payload MUST follow the Decision Export Contract.
- **FR-008**: `component-variants` MUST show all required component states, allow exactly one keyboard-persistent selected base variant plus a required reader-provided rationale, and expose visible controls labeled `Copy as prompt` and `Copy as Markdown`; its payload MUST follow the Decision Export Contract.
- **FR-009**: `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` MUST remain read-only and MUST NOT expose prompt, Markdown, copy, download, disabled export-looking controls, or other export affordances, including upstream-derived `Download SVG` controls.
- **FR-010**: Prompt and Markdown exports MUST derive from the live reader state in the exact Decision Export Contract order, name the conclusion and rationale, include enough context to act without reopening the page, reject incomplete decisions accessibly before calling the clipboard, announce copy results in text, reveal a focused selectable fallback containing the same payload when clipboard access is refused, and prevent stale copy attempts from replacing newer feedback. Clipboard refusal includes an unavailable Clipboard API, missing or non-callable `writeText`, a synchronous clipboard exception, a rejected write promise, denied permission, or a local-file security restriction; every refusal mode uses the same fallback path without retrying or reporting success.
- **FR-011**: Every intentional horizontal overflow region in shipped and newly completed artifacts MUST declare `data-rc-keyboard-scroll="horizontal"`, be sequentially focusable with `tabindex="0"`, use `role="group"`, and have a specific non-empty `aria-label`.
- **FR-012**: The five existing affected horizontal scroll containers in `code-approaches`, `implementation-plan`, and `module-map` MUST receive the declaration, keyboard focus, group role, and accessible-name repair required for new wide regions.
- **FR-013**: The gallery verification guard MUST sweep every manifest-shipped artifact, reject undeclared horizontal-overflow styling and noncompliant declared regions, prove the nine ART-004/repaired artifact IDs are included, and contain a synthetic negative fixture whose declared region omits its keyboard route; neither test nor fixture may be named after ART-004 or ART-020.
- **FR-014**: ART-004 MUST absorb ART-020 completely, mark ART-020 as superseded, keep one combined slice through specification, and stop for a human-approved split if the plan-time reviewability gate blocks the combined scope.
- **FR-015**: Every interactive control in the six new artifacts and the three
  repaired artifacts MUST be keyboard operable without pointer input, expose a
  visible focus indicator, avoid keyboard traps, and remain in a logical
  source-order focus sequence with no positive `tabindex` values. This includes
  direction/base-variant selection, background choice, padding slider,
  border/shadow controls, task completion, easing controls, drag/reorder or
  linked-screen controls, copy controls, fallback textarea, reset paths, theme
  control, and declared horizontal-scroll regions.
- **FR-016**: Every control and custom control group listed in FR-015 MUST have
  a programmatically determinable name, role, state, and value, plus visible
  labels or instructions where the reader enters or chooses data. `#export-status`
  MUST be a polite atomic live status region, fallback textarea controls MUST
  be labelled, invalid rationale state MUST be exposed with `aria-invalid`
  only while blank, and copy/status messages MUST not move focus except when
  clipboard refusal reveals and focuses the fallback textarea.
- **FR-017**: Both light and dark themes MUST keep all meaningful foreground,
  background, control, focus, status/error, and SVG/palette pairings within the
  audited brand-kit WCAG AA contract; normal text uses the 4.5:1 floor, large
  text and meaningful non-text indicators use the 3:1 floor, and no custom
  color pairing may be introduced without equivalent measurement. Color MUST
  NOT be the only carrier of selected, active, invalid, disabled/loading, drag
  insertion, SVG/palette, or theme/background meaning. When reduced motion is
  requested, template-added animation, transitions, smooth scrolling, and
  motion-like feedback MUST be removed or replaced while preserving the same
  visible state and control meaning.

### Functional Fidelity Inventory

The region names below are the source-of-truth keys for template inventory
comments and gallery fill-region validation. `feature-header` is sourced from
`spec.md`; every other region is sourced from `design-concept.md`.

| Artifact | Required fill regions |
|---|---|
| `visual-designs` | `feature-header`, `design-brief`, `background-toggle`, `directions` |
| `design-system` | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` |
| `component-variants` | `feature-header`, `variant-controls`, `variants`, `snippet-preview` |
| `animation-prototype` | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` |
| `interaction-prototype` | `feature-header`, `views`, `interaction-notes`, `open-questions` |
| `svg-illustrations` | `feature-header`, `illustrations`, `palette-rules` |

**Compaction boundary**:

- Preserve all four visual directions, all six component variant families, all
  three animation easing choices, every keyframe phase, all interaction notes
  and open questions, and all three SVG illustration concepts.
- Repeated design-system token rows, repeated card body copy, reorder-list
  sample rows beyond three reorderable rows, and repeated queue/shard SVG
  internals may be compacted only when the same token range, reorder behavior,
  or queue/retry/fan-out meaning remains observable.

**List slots and state-bearing elements**:

| Artifact | List slots | State-bearing elements |
|---|---|---|
| `visual-designs` | `directions` | Background choice and every stage theme |
| `design-system` | None | None beyond native wide-region focus/scroll state |
| `component-variants` | `variants` | Padding, border, shadow, hovered/selected variant, live snippet, rationale, and export state |
| `animation-prototype` | None | Completion toggle and selected easing |
| `interaction-prototype` | `views` | DOM order, dragging row, and insertion indicator |
| `svg-illustrations` | None | Inline SVG IDs used by internal references only; no export state |

**State visibility and reset requirements**:

- Every stateful control listed above MUST expose its current state in visible
  text, selected control state, or changed content before any export or UAT
  observation is accepted.
- Every stateful control listed above MUST expose a reset path when the state can
  persist in-page. The reset may be an explicit reset control or a
  source-faithful visible instruction, but the expected post-reset state must be
  observable without reading code.
- `visual-designs` current state is the checked background choice plus the
  visible stage theme. Selecting another background or direction visibly changes
  the active choice; no hidden persistence is required.
- `component-variants` current state is the `#pad-out` value, checked border
  option, checked shadow control, live card presentation, selected base variant,
  rationale field, and snippet text. Reset returns padding to `20px`, border to
  `hairline`, shadow to `shown`, clears transient hover-only emphasis, and
  refreshes the card/snippet/export context to match those defaults.
- `animation-prototype` current state is the visible done/not-done task row plus
  the active easing choice. Activating the task again resets the row to its
  initial not-done state while preserving the active easing choice.
- `interaction-prototype` current state is the visible order of retained views,
  the active dragging row, and the insertion indicator. Reset returns the list to
  the initial retained order; if the port translates upstream row reordering into
  linked screens, the active screen name is visible and reset returns to the
  first retained screen.
- Keyboard operation, focus visibility, names/roles/states, visible labels or
  instructions, live status, non-color meaning, both-theme contrast, and reduced
  motion remain acceptance requirements for every stateful control above. Native
  HTML controls are preferred; any custom control must declare its accessible
  role/state/value and keyboard behavior in markup or visible text.

**Load-bearing selector contract**:

- `visual-designs`: `#bg-seg`, `input[name="bg"]`, `.stage`, `.stage.dark`.
- `component-variants`: `#ctl-pad`, `#pad-out`,
  `input[name="border"]`, `#ctl-shadow`, `.card[data-snippet]`, `#snippet`.
- `animation-prototype`: `#task`, `.task.done`,
  `.ease-btn[data-ease]`, `.ease-btn.active`, `--ease`.
- `interaction-prototype`: `#list`, `.item[draggable="true"]`,
  `.item.dragging`, `#indicator`, `.indicator.on`.
- `svg-illustrations`: `svg#ill-queue`, `svg#ill-retry`,
  `svg#ill-fanout`.
- Exportable artifacts retain the exact visible labels `Copy as prompt` and
  `Copy as Markdown` and may reuse the shipped `#copy-prompt` and
  `#copy-markdown` ID pattern.
- `visual-designs` adds `input[name="chosen-direction"]`; the checked input
  resolves its owning direction and visible `.tag` label.
- `component-variants` adds `input[name="chosen-base-variant"]`; the checked
  input resolves its owning variant and visible `.variant-label` plus
  `data-snippet`/`#snippet` content.
- Both decision artifacts use a labeled `#rationale-field`, `#export-status`
  with `role="status"`, `aria-live="polite"`, and `aria-atomic="true"`,
  `#fallback`, and a labelled selectable `#fallback-field`.

### Decision Export Contract

Both formats use these common lines in this order:

1. `Artifact: <artifact title>`
2. `Feature: <feature id> <feature name>`
3. a blank line
4. the format- and artifact-specific lead sentence
5. a blank line
6. `<slot> / <selected visible label>  (#<anchor>)`
7. the artifact's live context lines in the order below
8. `Rationale: <trimmed reader rationale>`

The prompt lead is:

- `visual-designs`: `Implement the visual direction named below and no other. The value in parentheses is the anchor of the direction it names.`
- `component-variants`: `Implement the base component variant named below and no other. The value in parentheses is the anchor of the variant it names.`

The Markdown lead is:

- `visual-designs`: `Visual direction chosen while reviewing these options.`
- `component-variants`: `Base component variant chosen while reviewing these states.`

No additional Markdown syntax is added. `visual-designs` then emits
`Background: <light|dark>` and `Direction note: <visible direction note>`.
`component-variants` emits, in order:

1. `Variant note: <visible variant note>`
2. `States displayed: default, hover, focus, disabled, error, loading`
3. `Padding: <value>`
4. `Border: <value>`
5. `Shadow: <shown|hidden>`
6. `Snippet:` followed by the live snippet text

At invocation, each artifact reads the checked persistent decision radio,
resolves the visible label and note from its owning item, and reads the trimmed
rationale. `visual-designs` also reads `input[name="bg"]:checked`.
`component-variants` also reads `#pad-out`, the checked
`input[name="border"]`, `#ctl-shadow`, and the selected variant's live snippet.

If both choice and rationale are absent, announce
`Choose one option and enter a rationale before copying.` If only the choice is
absent, announce `Choose one visual direction before copying.` or
`Choose one base variant before copying.` If only the rationale is absent,
announce `Enter a rationale before copying.` Invalid attempts focus the first
missing control, set `aria-invalid="true"` only for a blank rationale, and do
not call the clipboard or expose fallback text.

Before a valid attempt, hide stale fallback content. An export-bearing state
change, reset, or invalid attempt after a revealed fallback MUST hide
`#fallback`, clear `#fallback-field`, and leave focus unchanged before the next
status message so an old payload is never visible beside a newer invalid or
changed state. On clipboard refusal, announce exactly `Copy failed. The text is
in the field below. Select it and copy it by hand.`, place the same live payload
in `#fallback-field`, reveal `#fallback`, and focus the textarea. Treat an
unavailable Clipboard API, missing or non-callable `writeText`, synchronous
exception, rejected write promise, denied permission, and local-file security
restriction as the same refusal outcome. Do not retry automatically, infer the
browser's reason, or report success for any refusal mode. An invocation counter
gates all delayed success/failure effects so an older attempt cannot move focus,
reveal stale text, or overwrite the newest status.

`#export-status` is not focused when its text changes; it exists only to expose
advisory success, invalid-input, failure, and stale-attempt outcomes to sighted
readers and assistive technologies. The fallback textarea is the only export
status path that intentionally receives focus, because the reader must be able
to select and copy the revealed payload manually.

### Keyboard-Scroll Guard Contract

The Layer 4 guard uses the existing standard-library `html.parser` collector.
It finds elements carrying `data-rc-keyboard-scroll="horizontal"` and asserts
that each has exactly `tabindex="0"`, exactly `role="group"`, and a trimmed,
non-empty, artifact-specific `aria-label`. It does not implement a CSS parser
or hard-code ART-020 selectors. A bounded raw-source check for horizontal
overflow styling rejects an artifact that declares no keyboard-scroll regions,
preventing the markup contract from passing vacuously.

The guard also rejects positive `tabindex` values in shipped gallery artifacts,
because sequential focus order must come from native controls and source order.
Its report records each declared region's artifact ID, source-order index, and
accessible name so manual Safari UAT can confirm the visible focus sequence
without relying on CSS order. Label checks reject absent, empty, or generic
names; the missing-`tabindex` negative fixture proves the keyboard-route
failure path, while the same guard assertions cover the naming path.

The RED fixture is constructed in the existing in-memory `GalleryFixtureCase`
style: one synthetic shipped artifact contains one declared horizontal region
with `role="group"` and a valid `aria-label` but no `tabindex`. The durable test
name is `test_rejects_declared_scroll_region_without_keyboard_route`. The guard
function keeps the repository convention that `gallery_root` is its first
argument.

Coverage is manifest-driven: all shipped artifacts are swept. A non-vacuity
assertion additionally requires the six ART-004 IDs and the three repaired IDs
(`code-approaches`, `implementation-plan`, `module-map`) in the checked set
after the planned status flips, and requires the five known existing regions to
be declared and compliant.

Manual UAT reuses ART-003's real-browser procedure: open the artifact through
`file://`, connect through CDP, focus the declared region, send the appropriate
horizontal arrow key, and observe a changed horizontal scroll position while
the accessible name remains exposed. ART-004 uses a separate target matrix and
result record; it never overwrites ART-003 harness outputs or results.

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
- Verification evidence MUST include the repository suite result, the global horizontal-scroll guard result, direct local-file/offline artifact checks, a manual UAT matrix with action, observable current-state outcome, and reset or cleanup outcome for every stateful interaction, export success and clipboard-refusal checks for the two decision artifacts, manifest-drift failure evidence, generated-artifact regeneration evidence with stale/missing/mismatched drift categories, and the plan-time reviewability gate result.
- Accessibility evidence MUST include keyboard operability, no keyboard traps,
  visible focus, names/roles/states/values, labels or instructions, polite live
  status, fallback focus, non-color meaning, reduced-motion behavior, and
  light/dark WCAG AA brand-kit contrast checks for the six new artifacts and
  the three repaired artifacts.
- Keyboard-scroll UAT evidence MUST reuse ART-003's real `file://`/CDP focus,
  arrow-key, and scroll-position procedure against the ART-004 target matrix and
  MUST be recorded separately without altering ART-003 results. Safari evidence
  MUST state whether Tab or Option-Tab was used according to the active Safari
  keyboard-navigation setting.
- Known gaps MUST explicitly state whether the combined slice passed the authoritative reviewability gate; if it did not pass, the PR must not proceed without the human-approved split.

### Key Entities *(include if feature involves data)*

- **Gallery Artifact**: A cataloged offline example page identified by a stable gallery identifier, status, category, stage, source metadata, usage text, and export declaration.
- **Pinned Upstream Source**: The source template file and commit used as the reproducibility baseline for each port.
- **Horizontal Overflow Region**: A wide content region that self-identifies with `data-rc-keyboard-scroll="horizontal"` because it can hide content horizontally and therefore requires sequential focus, a group role, a specific accessible name, and real-browser keyboard-scroll evidence.
- **Design Decision Export**: The live conclusion and rationale payload produced by `visual-designs` or `component-variants` as either prompt text or Markdown.
- **Reviewability Budget**: The declared scope, projected review surface, and split decision used to decide whether the combined slice may advance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All six planned design and prototyping catalog entries can be opened directly from the local file system while offline and inspected without missing a distinct upstream section or interaction.
- **SC-002**: Keyboard-only real-browser review reaches and changes the horizontal scroll position of 100% of declared wide regions in the five existing affected containers and every new artifact, while preserving each region's accessible name.
- **SC-003**: 100% of horizontal overflow regions in shipped gallery artifacts carry the declaration, focus, group-role, and naming contract; the global guard fails on the synthetic missing-`tabindex` fixture and proves all nine ART-004/repaired artifact IDs were swept.
- **SC-004**: For both exportable artifacts, a reader can complete selection, rationale entry, prompt copy, Markdown copy, incomplete-decision validation, clipboard-refusal fallback, and stale-copy-settle checks in under 3 minutes per artifact.
- **SC-005**: Catalog review confirms exactly six status changes from planned to shipped and zero unintended changes to identifiers, categories, stages, triggers, source metadata, when-to-use text, signal vocabulary, or export declarations.
- **SC-006**: Release review finds regenerated payloads, proofs, and generated reference artifacts aligned with the authored source changes, with no hand-edited generated mirrors; stale, missing, extra, truncated, rewritten, or byte-mismatched generated outputs are blocking validation failures.
- **SC-007**: Plan evidence either clears the authoritative reviewability gate for one combined slice or records a stop before task generation for a human-approved split.
- **SC-008**: Keyboard-only review can operate 100% of selection, slider,
  linked-screen or reorder, copy, fallback, reset, theme, and horizontal-scroll
  controls in logical focus order with visible focus and no trap, including the
  Safari keyboard-navigation path used for UAT.
- **SC-009**: Accessibility review confirms 100% of meaningful text,
  non-text/control indicators, focus indicators, status/error treatments, and
  SVG/palette annotations use audited light/dark brand-kit pairings or measured
  equivalents, convey meaning without color alone, and honor reduced-motion
  preference without losing state or control meaning.

## Assumptions

- The six gallery entries and the three existing affected shipped artifacts already exist in the catalog and can be updated without changing their identifiers or meaning.
- The pinned upstream source files remain accessible for planning and implementation evidence, but the upstream originals are not committed as gallery artifacts.
- Repeated sample groups may shrink only within the Functional Fidelity Inventory's compaction boundary; the remaining samples must still prove the same behavior or design range.
- Optional typeface substitution is acceptable when a reader is offline, provided the artifacts remain readable and usable through canonical brand-kit fallback stacks and do not rely on font-only glyphs for meaning.
- ART-001's canonical brand kit remains the accessibility source of truth for
  theme control behavior, focus-visible styling, contrast pairings, color-use
  rules, and reduced-motion defaults unless this feature states a stricter
  requirement.
- Empty rationale handling can guide the reader to provide a rationale before export rather than inventing rationale text.
- Generated release artifacts are derived from authoritative source after authored changes and are excluded from reviewability LOC accounting.
- No vertical-scroll or unrelated accessibility remediation is part of this feature.
