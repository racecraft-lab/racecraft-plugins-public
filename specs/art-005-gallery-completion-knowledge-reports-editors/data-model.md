# Data Model: ART-005 - Gallery Completion - Knowledge, Reports & Editors

## GalleryArtifact

Represents one standalone template opened from the local filesystem.

Fields:

- `id`: stable kebab-case identifier; one of `slide-deck`,
  `concept-explainer`, `status-report`, `incident-report`, `triage-board`,
  `feature-flags`, `prompt-tuner`
- `templatePath`: `speckit-pro/artifact-gallery/templates/<id>.html`
- `title`: manifest title
- `category`: manifest category
- `semanticRole`: `reader` or `producer`
- `status`: `planned` or `shipped`
- `exports`: `[]` for readers or `["markdown"]` for producers
- `upstreamSource`: reference to `UpstreamSourceBaseline`
- `fillInventory`: list of `FillSlot`
- `deliverySlice`: reference to `ReviewSlice`
- `interactionModel`: preserved upstream mechanism
- `accessibilityProfile`: summary of controls, focusable regions, semantic status
  regions, color/contrast evidence, and reduced-motion handling
- `responsiveProfile`: mobile and desktop review widths, page-level overflow
  result, and named-scroll exceptions
- `boundaryStateProfile`: empty, limit, invalid, dependency, and
  filtered-no-result states applicable to user-changeable surfaces
- `uatRows`: related `UATEvidenceRow` records

Validation rules:

- `templatePath` exists if and only if `status` is `shipped`.
- A reader has no export control and `exports: []`.
- A producer has exactly one `Copy as Markdown` control and `exports:
  ["markdown"]`.
- Each artifact embeds canonical `GALLERY-HEAD` and `BRAND-KIT` blocks exactly
  once when shipped.
- Every upstream-origin artifact carries a matching attribution header.
- Meaningful horizontal overflow regions follow the ART-020 focus/name/grouping
  pattern on the actual scroll element, and no artifact uses positive `tabindex`.
- The page itself has no horizontal overflow at 360 CSS px or at a desktop review
  width of at least 1280 CSS px, except for documented named scroll regions that
  have matching UAT evidence.
- Locally introduced color pairings either use audited Racecraft tokens or carry
  explicit light/dark contrast evidence before they convey text, control, focus,
  boundary, status, priority, warning, or error meaning.

State transitions:

- `planned` to `shipped` happens atomically with the template file, tests,
  generated payload refresh, and slice UAT evidence.
- No transition back to `planned` is planned.

## ReviewSlice

Represents one independently reviewable ART-005 delivery slice.

Fields:

- `sliceNumber`: integer from 1 through 7
- `branch`: planned branch name
- `predecessor`: prior `ReviewSlice` branch, or `null` for slice 1
- `artifactId`: one of the seven `GalleryArtifact.id` values
- `upstreamSource`: pinned upstream source file and digest for this slice
- `authoredOperations`: ordered list of the seven reviewability-counted authored
  path operations
- `generatedOperations`: ordered list of generated/check operation patterns and
  concrete paths expected for this artifact
- `projectedLocComponents`: component ledger with `markupContent`, `css`,
  `behaviorJs`, `incrementalTests`, and `total`
- `productionFileCount`: `1`
- `authoredFileCount`: `7`
- `maximumPhysicalPathFootprint`: `32`
- `verdict`: `pass`, `warn`, or `block`
- `uatIncrement`: slice-specific active UAT checks and rows
- `status`: `planned`, `implementing`, `blocked`, `pr_open`, `merged`, or
  `archived`

Validation rules:

- `sliceNumber`, `branch`, `predecessor`, and `artifactId` match the topology
  contract.
- `authoredOperations` always contains exactly one template operation, one
  manifest status flip, two test-module operations, and three active UAT file
  operations.
- `generatedOperations` are declared regeneration/check operations; byte-
  identical outputs are valid and must not be claimed as changed.
- `projectedLocComponents.total` equals the sum of all component fields and
  remains below 800 unless a ratified exception is recorded.
- If implementation measurement shows actual authored LOC plus remaining budget
  would reach 800 or more, the `status` becomes `blocked` before PR continuation.
- `maximumPhysicalPathFootprint` includes seven authored paths and up to 25
  generated/check paths, but generated paths are excluded from reviewable
  authored counts by the repository generated-artifact rule.

## ManifestEntry

Represents the catalog row routing an artifact.

Fields:

- `id`
- `category`
- `title`
- `when_to_use`
- `stage`
- `trigger`
- `source.origin`
- `source.file`
- `status`
- `exports`

Validation rules:

- `id` and `templatePath` agree by filename stem.
- `source.origin` remains `upstream` for all seven ART-005 entries.
- Only `status` changes in each slice.
- `stage` remains `ad-hoc`; `trigger` remains unchanged.
- Export arrays remain exactly as clarified.

## UpstreamSourceBaseline

Represents immutable source provenance for one artifact.

Fields:

- `repository`: `anthropics/html-effectiveness`
- `commit`: `58c305be97f47b26b678f2c07dec01d4242268ec`
- `commitTimestamp`: `2026-05-15T16:09:53Z`
- `retrievalDate`: `2026-08-17`
- `localEvidencePath`: scratch path outside the repository
- `sourceFile`
- `sha256`
- `lineCount`
- `byteCount`
- `preservedMechanism`

Validation rules:

- All seven sources use the same commit.
- Digests match the clarified spec before implementation uses the source.
- Upstream bytes are not copied into the repository.

## FillSlot

Represents one author-fillable region in a template.

Fields:

- `artifactId`
- `slotName`
- `fillsDescription`
- `sourceArtifacts`: values from the existing fill-region source vocabulary
- `isList`
- `minimumAnchoredItems`
- `anchorPattern`: `<slotName>-<item-slug>` for list slots

Validation rules:

- Each documented slot has exactly one flat marker pair in the body.
- Each body marker is documented in the inventory comment.
- List slots carry at least two anchored items unless a stricter requirement is
  recorded.
- Source names use the existing closed vocabulary in
  `test-artifact-fill-regions.py`.

## EditorSessionState

Represents live in-memory state for producer artifacts.

Fields:

- `artifactId`
- `visibleValues`
- `ordering`
- `currentSelections`
- `validationIssues`
- `derivedPreview`
- `resetSeed`
- `accessibilityState`: named controls, status region messages, focus target after
  movement or fallback, and keyboard-equivalent operations for pointer editing
- `boundaryState`: visible empty, limit, invalid, dependency, and
  filtered-no-result feedback for the editor's applicable controls and preview

Validation rules:

- State is initialized from representative sample data.
- State is not persisted in browser storage or URL.
- Reload resets editor content to the seed state.
- Export reads live state at invocation time.
- Pointer editing affordances have keyboard-operable equivalents that update the
  same visible state and export order.
- Dynamic success, failure, warning, dependency, movement, filter, validation, and
  editor-state messages update a programmatically determinable status region.
- Empty, limit, invalid, dependency, and filtered-no-result states are visible in
  text and, when caused by user action, update the same status-region mechanism.

## IssueRecord

Represents one deterministic issue attached to a producer export.

Fields, in serialized order:

- `code`: `empty_required_value`, `invalid_value`, `unavailable_value`, or
  `duplicate_identifier`
- `artifactId`: `triage-board`, `feature-flags`, or `prompt-tuner`
- `entityType`: `artifact`, `feature_flag_group`, `feature_flag`,
  `prompt_slot`, `prompt_sample`, or `triage_ticket`
- `entityId`: string or `null`
- `field`: declared schema field name
- `occurrenceIndex`: one-based integer or `null`
- `relatedOccurrenceIndex`: one-based first-occurrence index for duplicates, or
  `null`
- `rawValue`: exact original text, number, boolean, or `null`
- `normalizedValue`: string, number, boolean, or `null`
- `message`: exact stable human-readable message

Validation rules:

- `message` is determined by `code`: `Required value is empty.`, `Value is
  invalid and was not normalized.`, `A normalized value is unavailable.`, or
  `Identifier duplicates the first visible occurrence.`
- Issues are ordered by entity export order, declared field order, and condition
  order: empty, invalid, unavailable, duplicate.
- Duplicate issues attach to every occurrence after the first and preserve both
  the duplicate raw value and the first occurrence index.
- Raw invalid values are not clamped, truncated, coerced, sanitized, deduplicated,
  or renamed before export.

## MarkdownExport

Represents the text produced by a producer artifact.

Fields:

- `artifactId`
- `kind`: `markdown`
- `schemaVersion`: present for structured JSON editors
- `invocationOrdinal`
- `sourceStateSnapshot`: immutable per-invocation snapshot of current visible
  state
- `generatedText`: serialized exactly once from `sourceStateSnapshot`
- `issues`: ordered list of `IssueRecord`
- `jsonRoundTripText`: applicable to structured JSON editors during evidence
  capture

Validation rules:

- `triage-board` serializes columns in `now`, `next`, `later`, `cut` order and
  tickets in visible order.
- `triage-board` appends a deterministic `## Issues` section after `Cut`, using
  `- _No issues._` when empty.
- `feature-flags` emits one fenced JSON block with ordered groups, flags, and
  fields, plus ordered issues.
- `prompt-tuner` emits one fenced JSON block with ordered slots, visible
  samples, fields, live preview text, and ordered issues.
- Empty text is `""`; empty collections are `[]`; absent optional JSON fields
  are `null`; duplicate entries are preserved with deterministic `issues[]`
  records.
- Export text is not precomputed at page initialization, cached across
  invocations, or reused after visible state changes.
- Structured editor JSON parses successfully and reserializes with
  `JSON.stringify(value, null, 2)` to the exact JSON block emitted in Markdown.

## ClipboardAttempt

Represents one export invocation.

Fields:

- `artifactId`
- `invocationOrdinal`
- `sourceStateSnapshot`
- `exportText`
- `clipboardAvailable`
- `clipboardMethodState`: `absent`, `non_callable`, or `callable`
- `failureKind`: `none`, `unavailable`, `permission_denied`,
  `rejected`, or `synchronous_throw`
- `writeAttempted`
- `writeAttemptCount`: `0` or `1`
- `invokedControl`
- `priorStateCleared`
- `currentInvocation`
- `superseded`
- `settlement`: `pending`, `success`, or `fallback`
- `clipboardTextObserved`
- `fallbackTextObserved`
- `fallbackVisibleObserved`
- `fallbackSelectableObserved`
- `fallbackLabelObserved`
- `statusMessageObserved`
- `focusedTargetObserved`

Validation rules:

- At most one `navigator.clipboard.writeText()` attempt happens per invocation.
- Success message is `Copied. Markdown is on the clipboard.`
- Failure message is `Copy failed. The Markdown export is available below for
  manual copy.`
- Clipboard/object absence or an absent/non-callable method makes zero write
  attempts. Permission denial, generic rejection, and synchronous throw make one.
- Every failure class reveals and focuses a labeled selectable textarea
  containing the exact attempted string and uses the same exact failure message.
- A successful current invocation leaves its invoked control focused and leaves
  fallback content hidden and empty.
- A repeated current failure replaces fallback content with that invocation's
  exact export rather than appending or retaining stale text.
- Before each invocation, prior status, fallback visibility, and fallback text
  are cleared.
- Only the current invocation may update status, fallback text, fallback
  visibility, or focus; superseded settlements record their result without
  changing current UI state.
- Clipboard and fallback equality are byte-for-byte comparisons against that
  invocation's `exportText`.

## ErrorHandlingObservation

Represents one structured clipboard success, recovery, transition, or race UAT
observation.

Fields:

- `caseId`: `genuine_success`, `clipboard_absent`, `method_non_callable`,
  `permission_denied`, `generic_rejection`, `synchronous_throw`,
  `sequential_transition`, or `superseded_attempt`
- `clipboardMethodState`
- `failureKind`
- `writeAttemptCount`
- `attemptedExport`
- `clipboardTextObserved`
- `statusMessageObserved`
- `fallbackLabelObserved`
- `fallbackVisibleObserved`
- `fallbackSelectableObserved`
- `fallbackTextObserved`
- `focusedTargetObserved`
- `settlementOrder`
- `noStaleMutation`
- `notApplicableReason`

Validation rules:

- Every terminal state records exact status, fallback visibility/content, and
  focus rather than only a prose claim.
- Success and fallback text equality are byte-for-byte comparisons against the
  current invocation's `attemptedExport`.
- Sequential and superseded-attempt observations bind every recorded transition
  to an invocation ordinal and distinct live-state sentinel.

## UATEvidenceRun

Represents one durable acceptance run.

Fields:

- `featureId`
- `sourceCommit`
- `executedAt`
- `environment`
- `driver`
- `runbookPath`
- `rows`

Validation rules:

- `environment` records OS, browser name/version, `file://` scheme, network
  state, theme, reduced-motion, and color-mode conditions.
- `driver` is `manual` or the repository-relative harness path.
- The Markdown summary names the tested source commit and row totals.

## UATEvidenceRow

Represents one per-check result.

Fields:

- `artifactId`
- `templatePath`
- `step`
- `claim`
- `observedResult`
- `accessibilityObservation`
- `responsiveLayoutObservation`
- `boundaryStateObservation`
- `dataIntegrityObservation`
- `errorHandlingObservation`
- `verdict`: `pass`, `fail`, or `not_applicable`
- `date`
- `driver`

Validation rules:

- Every seven-artifact matrix check has a row.
- `not_applicable` includes an observation proving why the check does not apply.
- Editor rows distinguish real clipboard success from forced unavailable,
  rejected, and synchronous-throw fallback checks.
- Accessibility rows include structured focus-order, focused-fallback,
  scroll-region, status-region, and contrast-evidence fields where relevant.
- Scroll-region observations identify the actual overflow element, selector,
  `tabindex`, role or grouping semantic, accessible name, and overflow evidence.
- Responsive layout rows identify the viewport width, page horizontal-overflow
  result, clipped or overlapping text observation, and any named scroll-region
  exception.
- Boundary-state rows identify the triggered empty, limit, invalid, dependency, or
  filtered-no-result state, the visible message or inline cue, and the
  status-region message when dynamic feedback is expected.
- Data-integrity rows identify the exercised case, ordered inputs, baseline and
  attempted exports, JSON round-trip result, expected and observed order, issue
  records, stale/superseded attempt outcome, equality proof, or
  evidence-backed not-applicable reason.

## DataIntegrityObservation

Represents one structured data-integrity UAT observation.

Fields:

- `caseId`: `manifest_parity`, `live_export_freshness`, `empty_values`,
  `invalid_raw_value`, `unavailable_normalized_value`,
  `duplicate_identifiers`, `special_character_round_trip`,
  `multiple_issue_order`, `clipboard_exact_equality`, or
  `superseded_copy_attempt`
- `inputs`: ordered entries with `selector`, `field`, and `rawValue`
- `baselineExport`
- `attemptedExport`
- `comparison`: `differsFromBaseline`, `containsChangedValue`,
  `excludesReplacedValue`, and `exactClipboardOrFallbackEquality`
- `jsonRoundTrip`: `parsed`, `reserializedText`, `expectedText`, and `byteEqual`
- `expectedOrder`
- `observedOrder`
- `issues`: ordered `IssueRecord` records
- `supersededAttempt`
- `notApplicableReason`

Validation rules:

- Producer freshness rows compare a baseline export with a second export after a
  named visible value changes from a unique old sentinel to a unique new
  sentinel.
- Structured export rows parse the only JSON fence and require byte equality
  after `JSON.stringify(value, null, 2)`.
- Superseded-attempt rows cover older-success-after-newer-failure and
  older-failure-after-newer-success settlement orderings and prove the older
  attempt did not restore stale status, fallback content, fallback visibility, or
  focus.
