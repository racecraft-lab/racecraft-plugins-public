# Feature Specification: ART-005 - Gallery Completion - Knowledge, Reports & Editors

**Feature Branch**: `art-005-gallery-completion-knowledge-reports-editors`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Port seven planned knowledge, report, and editor gallery templates into complete standalone Racecraft artifacts, delivering them as seven independently reviewable stacked slices, resolving semantic export obligations from pinned upstream evidence, and delivering file:// UAT evidence."

## Clarifications

### Session 2026-08-17 - Source, Fidelity, and Fill Regions

- **Pinned identity:** Use
  `anthropics/html-effectiveness@58c305be97f47b26b678f2c07dec01d4242268ec`
  for all seven ports. The commit timestamp is `2026-05-15T16:09:53Z`; the
  evidence was retrieved from the official GitHub repository on `2026-08-17`.
- **Semantic classification:** `slide-deck`, `concept-explainer`,
  `status-report`, and `incident-report` are semantic readers and retain
  `exports: []`. Slide navigation and the concept explainer's transient
  add/remove/reset simulation do not produce a durable user-authored result
  meant to leave the SPA. `triage-board`, `feature-flags`, and `prompt-tuner`
  remain semantic producers with Markdown export.
- **Preservation boundary:** Preserve slide navigation, static report reading,
  the concept explainer's transient visualization controls, and the three
  editors' core editing controls. Intentionally add Racecraft branding,
  canonical embedded blocks, accessibility and fill-region conventions,
  deterministic Markdown exports for the three editors, memory-only state, and
  the contract fallback. Do not add download, import, persistence, URL, or
  server behavior.
- **Contract reconciliation:** No SPA-CONTRACT.md conflict remains after the
  classification above; the shared contract does not change.

| Upstream source | SHA-256 | Semantic role and preserved mechanism |
|---|---|---|
| `09-slide-deck.html` | `e191d49c28569e5f2ae09ed3bc4dc3f8ef25f90f1c842b1458f7b43ef5153291` | Reader; arrow-key/scroll slide navigation |
| `11-status-report.html` | `6468f720bab1d016657a9ed25c1049ec42f1810b230f486a5f3130427614bc7c` | Reader; static status-report reading |
| `12-incident-report.html` | `e787d6a64eca1ccd77fd9fa18849400356895ed2717ceb26dad2638fcc3261a9` | Reader; static incident timeline/report reading |
| `15-research-concept-explainer.html` | `5dd7d3a3866d123fdea1199a3e20d3a31d6305916013b4a2a4a83018765384b3` | Reader; transient consistent-hashing simulation |
| `18-editor-triage-board.html` | `a2a4ba2691c2532dbe67da5bbeb183bbdee5e9027c7006fba6dce18de7347988` | Producer; triage-board editing and Markdown feedback loop |
| `19-editor-feature-flags.html` | `8fd1aa16175614bea196672cd8f9b119b4ddb5b4768bf0bcb4bb05d6588787ab` | Producer; flag editing and Markdown feedback loop |
| `20-editor-prompt-tuner.html` | `b2e1e46643bb908cb01e73600f40a5506a175869a65ad446992f22eacd0b0877` | Producer; prompt editing and Markdown feedback loop |

The required fill-region floors are:

| Artifact | Required fill slots and minimum representative content |
|---|---|
| `slide-deck` | `deck-title`; `slides` list with at least 2 anchored items; `speaker-notes` |
| `concept-explainer` | `concept-title`; `principles`; `worked-example`; `simulation-scenarios` list with at least 2 anchored items |
| `status-report` | `summary`; `landed`, `in-flight`, `blocked`, and `next-actions` lists with at least 2 anchored items each |
| `incident-report` | `summary`; `timeline` list with at least 2 anchored items; `impact`; `root-cause`; `follow-ups` list with at least 2 anchored items |
| `triage-board` | `triage-items` list with at least 2 anchored items; `column-labels` |
| `feature-flags` | `flags` list with at least 2 anchored items; `environment-notes` |
| `prompt-tuner` | `prompt-variants` list with at least 2 anchored items; `evaluation-notes` |

### Session 2026-08-17 - Editor State and Export Contracts

- **Triage ordering:** Serialize columns in `now`, `next`, `later`, `cut`
  order, then tickets in their current visible order within each column. A
  complete export has this shape:

  ```markdown
  # Triage Board Export
  Artifact: triage-board
  Export kind: markdown

  ## Now
  Rationale: Blocking the current release or actively losing user data.
  - `T-101`
    - Title: Fix file:// copy fallback
    - Tag: bug
    - Estimate: S
    - Owner: Ana

  ## Next
  Rationale: High leverage and ready when Now clears.
  - _No tickets._

  ## Later
  Rationale: Valuable work that can wait for a future cycle.
  - `T-102`
    - Title: Unicode check - Zoë / 東京
    - Tag: qa
    - Estimate: M
    - Owner: -

  ## Cut
  Rationale: Close, deduplicate, or return to the requester.
  - `T-103`
    - Title: Remove duplicate export button
    - Tag: scope
    - Estimate: L
    - Owner: Sam
  ```

- **Feature-flag schema:** The Markdown wrapper contains exactly one fenced JSON
  block. Groups and flags stay in declared order. Object fields stay in the
  order shown; `requires` is a string or `null`, and `rollout` is a number or
  `null`, matching the pinned source model.

  ````markdown
  # Feature Flags Export
  Artifact: feature-flags
  Export kind: markdown

  ```json
  {
    "schemaVersion": "artifact-gallery.feature-flags.export.v1",
    "artifactId": "feature-flags",
    "groups": [
      {
        "id": "onboarding",
        "label": "Onboarding",
        "flags": [
          {
            "key": "onboarding.workspace_templates",
            "description": "Offer prebuilt workspace templates during signup.",
            "enabled": true,
            "requires": "onboarding.checklist_v2",
            "rollout": null
          }
        ]
      }
    ],
    "issues": []
  }
  ```
  ````

- **Prompt-tuner schema:** The Markdown wrapper contains exactly one fenced JSON
  block. Slots stay in the pinned order; samples stay in visible order; fields
  stay in slot order; preview text is the live derived value.

  ````markdown
  # Prompt Tuner Export
  Artifact: prompt-tuner
  Export kind: markdown

  ```json
  {
    "schemaVersion": "artifact-gallery.prompt-tuner.export.v1",
    "artifactId": "prompt-tuner",
    "template": "Reply to {{customer_name}} about {{ticket_subject}}.\nTone: {{tone}}",
    "slots": ["customer_name", "plan_tier", "ticket_subject", "ticket_body", "tone"],
    "samples": [
      {
        "id": "sample-1",
        "label": "SAMPLE 1",
        "planClass": "free",
        "fields": {
          "customer_name": "Priya",
          "plan_tier": "Free",
          "ticket_subject": "Missing board",
          "ticket_body": "I cannot find yesterday's board.",
          "tone": "warm and patient"
        },
        "preview": "Reply to Priya about Missing board.\nTone: warm and patient"
      },
      {
        "id": "sample-2",
        "label": "SAMPLE 2",
        "planClass": "team",
        "fields": {
          "customer_name": "Marcus",
          "plan_tier": "Team",
          "ticket_subject": "Sync dropped comments",
          "ticket_body": "Comments disappear between devices.",
          "tone": "direct and apologetic"
        },
        "preview": "Reply to Marcus about Sync dropped comments.\nTone: direct and apologetic"
      },
      {
        "id": "sample-3",
        "label": "SAMPLE 3",
        "planClass": "studio",
        "fields": {
          "customer_name": "Lena",
          "plan_tier": "Studio",
          "ticket_subject": "Billing entity",
          "ticket_body": "Use the new entity on the next invoice.",
          "tone": "brisk and friendly"
        },
        "preview": "Reply to Lena about Billing entity.\nTone: brisk and friendly"
      }
    ],
    "issues": []
  }
  ```
  ````

- **Edge representation:** Preserve empty text as `""`, empty collections as
  `[]`, and absent optional JSON fields as `null`. Preserve duplicate array
  entries in visible order and add a deterministic `issues[]` entry instead of
  deduplicating. Preserve the original raw value for invalid input, use `null`
  for any unavailable normalized value, and add an `issues[]` entry. Preserve
  multiline, Unicode, quotes, backticks, pipes, and other special characters;
  fenced JSON uses `JSON.stringify(value, null, 2)`, while triage field bodies
  use deterministic Markdown escaping and indented continuation lines.
- **Fresh export snapshots:** Every producer export invocation clears prior
  status/fallback text, hides and empties the prior fallback, captures one fresh
  immutable snapshot from the current visible state after the triggering UI
  change is applied, serializes that snapshot exactly once, and uses that exact
  string for clipboard equality or fallback. Export strings MUST NOT be
  precomputed at page initialization, cached across invocations, or regenerated
  differently for fallback than for clipboard. If an earlier asynchronous copy
  attempt settles after a later invocation, it records no current UI effect and
  MUST NOT replace the later status, fallback contents, fallback visibility, or
  focus target.
- **Issue records:** Structured editor `issues[]` entries, and the
  `triage-board` `## Issues` appendix, use this exact field order: `code`,
  `artifactId`, `entityType`, `entityId`, `field`, `occurrenceIndex`,
  `relatedOccurrenceIndex`, `rawValue`, `normalizedValue`, `message`. `code` is
  one of `empty_required_value`, `invalid_value`, `unavailable_value`, or
  `duplicate_identifier`. `artifactId` is one of the three producer IDs.
  `entityType` is `artifact`, `feature_flag_group`, `feature_flag`,
  `prompt_slot`, `prompt_sample`, or `triage_ticket`. `entityId`, `field`,
  `rawValue`, and `normalizedValue` are strings, numbers, booleans, or `null`
  as applicable; `occurrenceIndex` and `relatedOccurrenceIndex` are one-based
  integers or `null`. Stable messages are: `Required value is empty.`, `Value is
  invalid and was not normalized.`, `A normalized value is unavailable.`, and
  `Identifier duplicates the first visible occurrence.`
- **Issue ordering:** When multiple issues exist, emit them by traversing
  entities in export order, fields in declared schema order, and conditions in
  this order: `empty_required_value`, `invalid_value`, `unavailable_value`,
  `duplicate_identifier`. Duplicate issues attach to every occurrence after the
  first and set `relatedOccurrenceIndex` to the first visible occurrence. Issue
  ordering never depends on arbitrary object-key enumeration.
- **Duplicate and raw invalid handling:** Duplicate feature-flag group IDs, flag
  keys, prompt slot identifiers, prompt sample identifiers, and triage ticket IDs
  remain in visible/export order and are not deduplicated or renamed. Invalid
  rollout or dependency input preserves its exact original text in `rawValue`;
  the normalized exported field and issue `normalizedValue` are `null`, with no
  clamping, truncation, coercion, or sanitization. Prompt `slots` preserves
  duplicate/raw strings; each sample's `fields` object contains each distinct
  slot key once, in first-occurrence slot order, with duplicates represented by
  `slots` and issue records. Multiline text, Unicode, quotes, backticks, pipes,
  slash, backslash, tab, newline, and other special characters round-trip
  through the fenced JSON or triage Markdown without data loss. `triage-board`
  appends `## Issues` after `Cut`, using `- _No issues._` when empty and JSON
  scalar representation for issue string/null values.
- **Clipboard behavior:** Each editor has exactly one control labeled
  `Copy as Markdown`. On every invocation, read `navigator.clipboard` afresh,
  clear prior status/fallback state, generate the export once from live state,
  and call `writeText()` at most once only when it is callable. An absent
  clipboard object or absent/non-callable `writeText` is unavailable and makes
  no write attempt. Success announces `Copied. Markdown is on the clipboard.`,
  leaves the invoked control's focus unchanged, and leaves the fallback hidden
  and empty. Unavailability, a permission-denied rejection such as
  `NotAllowedError`, any other rejected promise, or a synchronous throw all
  announce only `Copy failed. The Markdown export is available below for manual
  copy.`, reveal a labeled selectable textarea containing the exact attempted
  string, and focus it. Browser exception text is not exposed as the user-facing
  message. A later current attempt replaces, rather than appends to, any prior
  fallback; hidden copy, silent failure, and download recovery are prohibited.

### Session 2026-08-17 - Acceptance Evidence and Reviewability

- **Evidence locations:** During active work, keep the plain-English runbook at
  `.process/uat-runbook.md` inside this feature directory. Keep the human-readable
  result summary at `.process/uat-results.md` and the normalized per-check record
  at `.process/uat-results.json`. Post-merge archival preserves them as
  `docs/ai/specs/.process/ART-005-uat-runbook.md`,
  `docs/ai/specs/.process/ART-005-uat-results.md`, and
  `docs/ai/specs/.process/ART-005-uat-results.json`; a committed browser harness,
  if implementation proves one necessary, keeps its detailed JSON under an
  `ART-005-uat-harness/` directory beside those files.
- **Run metadata:** The normalized result record has top-level `featureId`,
  `sourceCommit`, `executedAt`, `environment`, `driver`, and `runbookPath` fields.
  `environment` identifies operating system, browser name/version, `file://`
  scheme, and the network, theme, reduced-motion, and color-mode conditions used.
  `driver` is `manual` or the repository-relative path of the exact harness.
- **Cumulative source binding:** Before each slice executes UAT, commit the
  current source, manifest, focused tests, generated outputs, and existing UAT
  carrier files as a source checkpoint. Re-execute every carried-forward row for
  all artifacts shipped through that slice, then set the top-level
  `sourceCommit` to that checkpoint. No row from an older source commit may be
  retained under a newer top-level `sourceCommit`. Record the resulting evidence
  in a later commit so the checkpoint hash exists before it is cited.
- **Per-check evidence:** Every result row has `artifactId`, `templatePath`,
  `step`, `claim`, `observedResult`, optional `accessibilityObservation`,
  optional `responsiveLayoutObservation`, optional `boundaryStateObservation`,
  optional `dataIntegrityObservation`, optional `errorHandlingObservation`,
  `verdict`, `date`, and `driver`.
  `verdict` is `pass`, `fail`, or `not_applicable`; `not_applicable` still
  requires an observation proving why the check does not apply. The Markdown
  summary reports totals and identifies the exact source commit represented by
  the JSON rows.
- **Clipboard proof:** Each editor requires one genuine `file://` success in
  which a real clipboard read-back or paste exactly equals the live-state export,
  the success message is present, the fallback is hidden and empty, and focus is
  not moved away from the invoked control. Separate checks force an absent
  clipboard object, an absent/non-callable method, permission-denied rejection,
  generic rejected promise, and synchronous throw, and prove that every path
  makes zero or one write attempt as applicable, reveals and focuses the exact
  fallback text, and never reports success. The unavailable probe uses
  `Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true});`;
  `delete navigator.clipboard` is prohibited because the inherited accessor makes
  that expression a no-op and can produce a false pass. A sequential
  failure-success-failure check proves status, fallback visibility/content, and
  focus always reflect the latest invocation; the two opposite delayed-settlement
  races prove superseded attempts cannot mutate current UI state.
- **Seven-artifact matrix:** Every artifact receives result rows for direct
  `file://` open, complete representative content, offline reload, complete
  keyboard traversal, visible focus, light/dark theme parity, reduced-motion
  behavior, and color-independent meaning. A named keyboard-focusable horizontal
  scroll region is verified wherever one exists; its absence is recorded as
  `not_applicable` with the observed layout. The three editors additionally
  receive live-state serialization, genuine clipboard success, and all three
  forced-fallback checks.
- **Data-integrity evidence matrix:** Every artifact receives manifest parity
  rows that bind ID, source file, status, role, and export declaration to the
  exhaustive ART-005 table. Every producer receives rows for live export
  freshness, empty values/collections, duplicate identifiers, special-character
  round-trip, multiple simultaneous issue ordering, exact clipboard/fallback
  equality, and superseded copy attempts in both settlement directions. Relevant
  structured editor rows also cover raw invalid input and unavailable normalized
  values. Reader-only entries record producer-only data-integrity cases as
  evidence-backed `not_applicable`. For structured exports, UAT extracts the sole
  JSON fence, parses it, reserializes it with `JSON.stringify(value, null, 2)`,
  and records byte equality with the original JSON block.
- **Reviewability response:** The combined plan-time projection reached the
  800-LOC block and stopped before Checklist, Tasks, or Implementation. The
  operator resolved that stop by selecting seven slices. Planning now measures
  every slice independently and stops only the affected slice if its final
  projection reaches a block threshold without a ratified exception.

### Session 2026-08-17 - Review Topology Resolution

- **Operator decision:** Deliver ART-005 as seven sequential review slices, one
  template per slice, while retaining one specification and one workflow.
- **Slice order:** (1) `slide-deck`, (2) `concept-explainer`, (3)
  `status-report`, (4) `incident-report`, (5) `triage-board`, (6)
  `feature-flags`, and (7) `prompt-tuner`.
- **Stacking model:** Slice 1 uses the current feature branch. Each later slice
  is cut from its predecessor after the predecessor's PR is open. Planning does
  not create those branches or merge any slice.
- **Atomic slice boundary:** Each slice contains its one template, that
  template's own manifest status flip, its incremental Layer 4 and fill-region
  coverage, authoritative payload and reference regeneration, and slice-specific
  UAT evidence. Shared manifest, test, generated, and evidence files are changed
  serially in stack order.
- **Per-slice gate:** Planning MUST project each slice independently. A measured
  block stops only that slice for an explicit operator decision; this topology
  does not authorize splitting a template or inventing a reviewability exception.

### Session 2026-08-17 - Accessibility Contract Detail

- **Scroll-region prevention:** Any meaningful horizontal overflow container MUST
  follow the ART-020 gallery pattern: the actual element with `overflow-x` is in
  normal focus order with `tabindex="0"`, carries grouping semantics such as
  `role="group"`, has a non-empty programmatic name through `aria-label` or
  `aria-labelledby`, and does not delegate focus to a wrapper or descendant. No
  ART-005 artifact may use a positive `tabindex`.
- **Contrast and color meaning:** Locally introduced colors MUST either reuse
  audited Racecraft token pairings from the gallery brand kit or carry explicit
  contrast evidence for both light and dark themes. Normal text clears 4.5:1;
  large text, focus indicators, controls, meaningful boundaries, and meaningful
  graphics clear 3:1. `--rc-border-subtle` remains decorative only and cannot
  carry state, grouping, priority, warning, or error meaning by itself.
- **Status semantics:** Dynamic success, failure, warning, dependency, movement,
  filter, validation, and editor-state messages MUST update a persistent
  programmatically determinable status region, using `role="status"` or an
  equivalent live-region semantic. The visible message remains text, and the
  clipboard failure path still moves focus to the labeled fallback textarea.
- **Slide navigation:** `slide-deck` MUST expose a named navigation group with
  named previous/next controls or named direct-slide controls, current position
  text such as `Slide X of Y`, no auto-rotation, and deterministic focus behavior.
  Control-invoked slide changes keep focus on the invoked control while updating
  the current-position text; non-control slide changes move focus to the active
  slide's named heading or container. Hidden slides are excluded from sequential
  focus and the accessibility tree.
- **Triage-board controls:** `triage-board` MUST expose the board, each column,
  each ticket, filters, reset, and export affordances with programmatic names.
  Any pointer drag/drop movement or priority/filter interaction preserved from
  upstream MUST have a keyboard-operable equivalent for moving tickets between
  columns and reordering them within a column. Movement and filtering update
  visible order immediately, keep focus on the moved ticket or movement control,
  and announce the resulting column, position, or filter state through the status
  region.
- **Structured UAT evidence:** Accessibility UAT rows MUST keep the human-readable
  `observedResult` and, where applicable, add structured observations for focus
  order, focused fallback target, scroll-region selector/role/name/tabindex,
  actual scroll element, status-region semantics, and contrast evidence source or
  measured ratios.

### Session 2026-08-17 - UX Boundary And Responsive Criteria

- **Visible boundary states:** User-changeable ART-005 surfaces MUST expose empty,
  limit, invalid, dependency, and filtered-no-result states in visible text and,
  when the state changes dynamically, through the applicable status region rather
  than relying on color, disabled controls, or silent clamping alone.
  `concept-explainer` shows current node/key counts and min/max control limits;
  add/remove or slider actions at a limit leave the simulation state unchanged and
  update helper or status text. `triage-board` shows explicit empty-column text
  and an explicit filtered-no-result message when a filter hides every ticket in a
  column or across the board. `feature-flags` shows dependency, invalid, empty, or
  unavailable normalized values beside the affected flag, group, or preview.
  `prompt-tuner` shows empty template, slot, sample, and derived-preview values as
  intentional empty strings and surfaces duplicate or invalid slot issues visibly.
- **Responsive review bounds:** Every artifact MUST remain readable and operable
  at a 360 CSS px mobile review width and a desktop review width of at least 1280
  CSS px, with no clipped or overlapping text and no page-level horizontal
  overflow. Horizontal scrolling is permitted only inside named, meaningful
  regions that satisfy the ART-020 focus/name/grouping pattern and carry UAT
  evidence.

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
- **FR-002**: The feature MUST use the immutable upstream commit and seven SHA-256 source identities recorded in Clarifications as the baseline for all seven ports.
- **FR-003**: Each artifact MUST preserve the core upstream content or interaction model while applying Racecraft branding, canonical embedded gallery blocks, the single-file contract, accessibility obligations, and gallery fill-region conventions.
- **FR-004**: Each shipped artifact MUST be delivered atomically with its own catalog entry status changed from `planned` to `shipped`; no other catalog value may change unless required by the resolved export classification.
- **FR-005**: `slide-deck`, `concept-explainer`, `status-report`, and `incident-report` MUST remain semantic readers with `exports: []`; their pinned navigation, static reading, and transient simulation controls do not produce durable user-authored output meant to leave the SPA.
- **FR-006**: Any artifact confirmed as a semantic reader MUST carry no export control and MUST retain an empty export declaration.
- **FR-007**: The three known editor artifacts, `triage-board`, `feature-flags`, and `prompt-tuner`, MUST retain `markdown` as their only export kind and MUST label the export control exactly `Copy as Markdown`.
- **FR-008**: `feature-flags` and `prompt-tuner` exports MUST be deterministic Markdown documents containing lossless structured session state in one fenced JSON block with the exact versioned schemas, wrapper/group/flag/sample/issue field order, collection order, issue ordering, and edge-value rules recorded in Clarifications.
- **FR-009**: `triage-board` exports MUST use the exact human-readable, column-grouped Markdown shape, declared column order, current ticket order, empty-column representation, deterministic issue appendix, duplicate-ticket reporting, and escaping rules recorded in Clarifications.
- **FR-010**: Every export MUST be generated from one fresh immutable snapshot of the artifact's live visible state at the moment the operator invokes it; precomputed or cross-invocation cached export strings are prohibited.
- **FR-011**: Each editor MUST implement the invocation-time capability check, zero-or-one-attempt clipboard success, normalized visible focused fallback for every declared failure class, stale-state clearing/replacement, current-invocation focus behavior, and superseded-attempt suppression recorded in Clarifications; hidden `execCommand` copying, silent failure, and automatic download are prohibited.
- **FR-012**: Editor working state MUST be memory-only and reset on reload; existing gallery theme preference behavior MUST remain unaffected.
- **FR-013**: Every new artifact MUST open directly over `file://`, remain readable with no server or install step, and avoid missing content when the network is unavailable.
- **FR-014**: Every new artifact MUST satisfy the accessibility contract detail recorded in Clarifications: new horizontal scroll regions use the exact ART-020 focus/name/grouping pattern, controls have visible focus and accessible names, dynamic status is programmatically determinable text, reduced motion removes required animation/transition/smooth-scroll behavior, color is never the sole carrier of meaning, and locally introduced color pairings are either audited Racecraft tokens or explicitly measured for both themes.
- **FR-015**: The feature MUST preserve the tracked plain-English `file://` UAT runbook, Markdown result summary, and normalized per-check JSON record at the active-feature and archival paths, with the mandatory metadata, row fields, verdicts, and seven-artifact coverage recorded in Clarifications.
- **FR-016**: Planning MUST include a file-by-file measurement of the pinned upstream sources and declared operations before implementation starts; each slice MUST separately report its seven implementation-authored paths, any `tasks.md` control-plane checkbox path, every changed generated path, authored reviewable LOC, and the full physical Git-path count.
- **FR-017**: If any slice's authored implementation projection crosses a reviewability block threshold, or any full-diff reviewability result contains a correctness or non-size safety blocker, planning or implementation MUST stop that slice for an operator topology decision instead of splitting the template automatically or inventing an exception. A full-diff total-file block caused solely by required source-derived generated paths and the separately reported `tasks.md` control-plane path MUST be recorded as a size-only block and carried through the already-ratified seven-branch review topology; it is not a typed exception and does not authorize another topology change.
- **FR-018**: The feature MUST use the selected seven-slice topology, one template per sequential stacked review slice in the recorded order, unless an explicit later operator decision changes that topology.
- **FR-019**: The feature MUST NOT add workflow-stage routing, JSON export kinds, automatic downloads, import-back, persistent editor content, shareable URL state, server storage, shared gallery foundation changes, or repairs to already-shipped templates.
- **FR-020**: Each artifact MUST implement the exact fill-slot inventory and minimum anchored sample-content floors recorded in Clarifications; list slots MAY exceed their floor only when the template markers and Layer 4 inventory remain in agreement.
- **FR-021**: User-changeable ART-005 surfaces MUST implement the visible boundary-state contract recorded in Clarifications for empty, limit, invalid, dependency, and filtered-no-result states.
- **FR-022**: Every new artifact MUST satisfy the responsive review bounds recorded in Clarifications at 360 CSS px and at a desktop width of at least 1280 CSS px, with page-level horizontal overflow prohibited except for documented named scroll regions.
- **FR-023**: Producer exports MUST preserve raw and normalized issue evidence for empty, invalid, unavailable, duplicate, and special-character conditions using the issue-record schema and deterministic ordering recorded in Clarifications; values MUST NOT be clamped, truncated, coerced, sanitized away, deduplicated, or renamed.
- **FR-024**: The UAT evidence record MUST include structured data-integrity observations for manifest/export parity, live export freshness, edge-case round-trips, issue ordering, exact per-attempt clipboard/fallback equality, and superseded copy attempts.

### Reviewability Notes *(if applicable)*

- No ratified reviewability exception exists for this feature.
- The operator initially selected one combined slice after being shown that both
  estimates warned and suggested two slices. The measured combined projection
  later blocked, and the operator superseded that answer with seven slices.
- Generated templates, generated zones, process files, PR bodies, and code fences are not valid provenance for a typed reviewability exception. Recording a generated/control-plane-only total-file block as size-only is routing evidence, not an exception.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (shipped gallery artifacts)
- **Secondary surfaces, if any**: N/A
- **Preset thresholds**: Warn above 400 reviewable LOC, above 6 production files, above 15 total files, or above 1 primary surface. Block above 800 reviewable LOC, above 8 production files, above 25 total files, or above 1 primary surface without a ratified exception.
- **Projected reviewable LOC**: Roadmap estimate 560 LOC; scaffold estimate 555 LOC. Both estimates warn and suggest two slices because they exceed the 400 reviewable LOC warning threshold and remain below the 800 reviewable LOC block threshold.
- **Projected production files**: 7 net-new artifact files, which exceeds the preset warning threshold of 6 production files and remains below the block threshold of 8 production files.
- **Projected total files**: Approximately 9 authored files before generated mirrors, below the total-file warning threshold of 15.
- **Measured combined result**: Seven pinned sources total 4,042 lines and
  120,618 bytes. The conservative combined projection is 2,856 reviewable LOC,
  and the ART-003-average projection is 4,356; both exceed the 800-LOC block.
- **Split decision**: The feature remains one ART-005 spec and workflow but is
  delivered as seven sequential stacked slices, one template per slice, in the
  order recorded above. Planning must measure each slice's declared operations
  independently. Every slice has seven implementation-authored paths, up to 25
  source-derived generated/check paths, and one possible `tasks.md` control-plane
  path, for a maximum physical footprint of 33 paths. That maximum exceeds the
  25-file full-diff block and is therefore a projected size-only routing risk,
  not an unqualified pass. Authored or non-size blockers stop; a block caused
  only by required generated/control-plane paths is recorded in the slice packet
  and continues through the already-ratified seven-branch topology.

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
- **Data Integrity Issue**: A deterministic record attached to a producer export
  when visible data is empty, invalid, unavailable, or duplicated; key
  attributes are stable code, entity locator, occurrence indexes, raw value,
  normalized value, and exact message.
- **Manual Copy Recovery**: The fallback path used when clipboard copy fails; key attributes are visible status, labeled selectable field, exact export text, and focus movement.
- **UAT Evidence Record**: The durable acceptance record for `file://` checks; top-level attributes bind the feature, tested commit, execution time, environment, driver, and runbook, while each row binds an artifact and template path to a step, claim, observed result, verdict, date, driver, and applicable accessibility, responsive-layout, boundary-state, data-integrity, or error-handling observations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven ART-005 catalog entries can be opened directly over `file://` and present complete representative content with no missing artifact content.
- **SC-002**: The manifest and artifact files agree for 100% of the seven entries: each shipped entry has its artifact, and no ART-005 artifact remains planned.
- **SC-003**: For all three known editors, changing visible state before `Copy as Markdown` changes the exported Markdown deterministically to match the current session state.
- **SC-004**: For all three known editors, forced absent/non-callable clipboard access, permission denial, generic rejection, and synchronous failure each expose and focus a labeled selectable manual-copy field containing the exact attempted export after no more than one write attempt.
- **SC-005**: Keyboard-only UAT covers all seven artifacts and verifies reachable named scroll regions where present, visible focus on controls, and no color-only status or priority meaning.
- **SC-006**: Reduced-motion UAT verifies that all seven artifacts remain usable without required animation, transition, or smooth-scroll behavior.
- **SC-007**: The tracked UAT result record contains a `pass`, `fail`, or evidence-backed `not_applicable` row for every required check across all seven artifacts, including structured accessibility and error-handling observations where applicable plus genuine clipboard success, every declared forced-fallback class, the sequential failure-success-failure transition, and both superseded-attempt races for each editor.
- **SC-008**: The plan-time reviewability record preserves both warned estimates and the measured combined block, records the explicit seven-slice operator decision, and provides file-by-file declared operations plus an independently evaluated projection for every slice.
- **SC-009**: UAT covers the visible boundary-state contract for `concept-explainer`, `triage-board`, `feature-flags`, and `prompt-tuner`, including empty, limit, invalid, dependency, and filtered-no-result cases where applicable.
- **SC-010**: UAT covers every artifact at 360 CSS px and at a desktop width of at least 1280 CSS px, with no clipped or overlapping text and no page-level horizontal overflow except documented named scroll regions.
- **SC-011**: Every producer passes freshness, empty-value, duplicate-identifier,
  special-character, multiple-issue-order, exact clipboard/fallback equality, and
  superseded-attempt UAT checks; `feature-flags` and `prompt-tuner` also pass
  raw-invalid and unavailable-normalization checks.
- **SC-012**: For each structured editor export, extracting the sole JSON fence,
  parsing it, and reserializing it with `JSON.stringify(value, null, 2)` produces
  the exact original JSON block with the expected collection, field, and issue
  ordering.

## Assumptions

- The target reader or operator opens gallery artifacts from a local filesystem and does not rely on a local server.
- Representative sample content is acceptable for all seven artifacts as long as it preserves the upstream content or interaction model and is complete enough for UAT.
- The immutable upstream commit and file digests are resolved during planning rather than guessed in the specification.
- The existing gallery theme preference behavior remains owned by the shared canonical block and is not redesigned by ART-005.
- Functional fidelity means preserving the recognizable content model and interaction purpose of each upstream file, not pixel-perfect upstream styling.
- Generated payload copies and installed-cache proofs are handled by authoritative repository tooling after source changes; this specification does not authorize hand-editing generated mirrors.
