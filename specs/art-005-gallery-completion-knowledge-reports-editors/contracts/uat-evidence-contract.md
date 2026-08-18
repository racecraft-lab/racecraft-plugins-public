# Contract: UAT Evidence

ART-005 preserves active UAT evidence during implementation and archives it
after merge.

## Active Paths

```text
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md
specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json
```

The files grow serially in slice order. Slice 1 creates them; slices 2 through 7
modify them.

## Archival Paths

```text
docs/ai/specs/.process/ART-005-uat-runbook.md
docs/ai/specs/.process/ART-005-uat-results.md
docs/ai/specs/.process/ART-005-uat-results.json
docs/ai/specs/.process/ART-005-uat-harness/
```

The harness directory is used only if implementation proves a committed browser
harness necessary.

## JSON Run Schema

Top-level fields:

- `featureId`
- `sourceCommit`
- `executedAt`
- `environment`
- `driver`
- `runbookPath`
- `rows`

`environment` includes:

- operating system
- browser name and version
- `file://` scheme
- network condition
- theme condition
- reduced-motion condition
- color-mode condition

`driver` is `manual` or the repository-relative path of the exact harness.

## Row Schema

Every row has:

- `artifactId`
- `templatePath`
- `step`
- `claim`
- `observedResult`
- `accessibilityObservation` when the row covers keyboard, focus, scroll-region,
  status, contrast, reduced-motion, or clipboard fallback focus evidence;
  otherwise `null` or omitted
- `responsiveLayoutObservation` when the row covers mobile or desktop responsive
  review; otherwise `null` or omitted
- `boundaryStateObservation` when the row covers empty, limit, invalid,
  dependency, or filtered-no-result feedback; otherwise `null` or omitted
- `dataIntegrityObservation` when the row covers manifest parity, live export
  freshness, edge serialization, issue ordering, clipboard/fallback equality, or
  stale/superseded copy attempts; otherwise `null` or omitted
- `errorHandlingObservation` when the row covers clipboard success, a forced
  recovery class, a sequential transition, or a superseded attempt; otherwise
  `null` or omitted
- `verdict`
- `date`
- `driver`

`verdict` is `pass`, `fail`, or `not_applicable`. A `not_applicable` verdict
still includes an observation proving why the check does not apply.

`accessibilityObservation`, when present, is an object with only the relevant
fields for that row:

- `focusOrder`: ordered entries with `selector`, `role`, `name`, and visible
  focus indicator evidence for every traversed stop
- `focusedFallbackTarget`: selector, role, accessible name, focused state, and
  equality proof against the attempted export text
- `scrollRegions`: entries with selector, role, accessible name, `tabindex`,
  horizontal-overflow evidence, and `actualScrollElement`
- `statusRegions`: entries with selector, role or live-region semantic, exposed
  message text, and covered message kinds
- `contrastEvidence`: audited token source or explicit light/dark measurements
  for any locally introduced text, control, focus, boundary, or meaningful
  non-text color pairing
- `notApplicableReason`: structured reason when an accessibility field does not
  apply to the row

`responsiveLayoutObservation`, when present, records:

- `viewportWidthCssPx`: `360` for mobile review or a desktop width of at least
  `1280`
- `pageHorizontalOverflow`: observed boolean or measured result
- `clippedOrOverlappingText`: observed boolean plus selector or screenshot note
  when present
- `namedScrollExceptions`: any permitted horizontal scroll regions and their
  selector/name evidence

`boundaryStateObservation`, when present, records:

- `stateKind`: `empty`, `limit`, `invalid`, `dependency`, or
  `filtered_no_result`
- `artifactState`: the visible input, filter, editor, preview, or control state
  that triggered the observation
- `visibleFeedback`: exact visible text or inline cue shown to the user
- `statusRegionFeedback`: exact status-region text when the state changes
  dynamically, or `not_applicable` with a reason

`dataIntegrityObservation`, when present, records:

- `caseId`: `manifest_parity`, `live_export_freshness`, `empty_values`,
  `invalid_raw_value`, `unavailable_normalized_value`,
  `duplicate_identifiers`, `special_character_round_trip`,
  `multiple_issue_order`, `clipboard_exact_equality`, or
  `superseded_copy_attempt`
- `inputs`: ordered entries with selector, field, and raw value
- `baselineExport` and `attemptedExport` when comparing export freshness
- `comparison`: booleans for `differsFromBaseline`, `containsChangedValue`,
  `excludesReplacedValue`, and `exactClipboardOrFallbackEquality`
- `jsonRoundTrip`: parsed status, reserialized text, expected text, and byte
  equality for structured JSON exports
- `expectedOrder` and `observedOrder` for collections, fields, tickets, or issue
  records
- `issues`: ordered issue records using the editor export contract schema
- `supersededAttempt`: settlement order and proof that an older attempt did not
  restore stale status, fallback content, fallback visibility, or focus
- `notApplicableReason` for evidence-backed non-applicability

`errorHandlingObservation`, when present, records:

- `caseId`: `genuine_success`, `clipboard_absent`, `method_non_callable`,
  `permission_denied`, `generic_rejection`, `synchronous_throw`,
  `sequential_transition`, or `superseded_attempt`
- `clipboardMethodState`: `absent`, `non_callable`, or `callable`
- `failureKind`: `none`, `unavailable`, `permission_denied`, `rejected`, or
  `synchronous_throw`
- `writeAttemptCount`: `0` or `1`
- `attemptedExport` and `clipboardTextObserved`
- exact `statusMessageObserved`
- `fallbackLabelObserved`, `fallbackVisibleObserved`,
  `fallbackSelectableObserved`, and `fallbackTextObserved`
- `focusedTargetObserved`
- `settlementOrder` and `noStaleMutation` for transition/race rows
- `notApplicableReason` for evidence-backed non-applicability

## Required Matrix

Every artifact has rows for:

- direct `file://` open
- complete representative content
- offline reload
- complete keyboard traversal
- visible focus
- light/dark theme parity
- reduced-motion behavior
- color-independent meaning
- named keyboard-focusable horizontal scroll region where present
- responsive layout at 360 CSS px and at a desktop width of at least 1280 CSS px

Accessibility rows record enough structured evidence to prove the relevant
requirement without relying on prose alone. For scroll-region rows, the actual
element with horizontal overflow carries `tabindex="0"`, grouping semantics, and
a programmatic name; if no meaningful horizontal overflow exists, the row is
`not_applicable` and records the observed layout reason.

Every editor additionally has rows for:

- live-state serialization
- genuine clipboard success with read-back or paste equality
- forced unavailable clipboard fallback
- forced absent/non-callable method fallback
- permission-denied rejection fallback
- generic rejected-promise fallback
- synchronous throw fallback
- failure-success-failure sequential transition with distinct live-state values
- empty, invalid, dependency, and unavailable-value feedback where applicable
- manifest parity against the exhaustive ART-005 ID/source/role/status/export
  table
- live export freshness using a baseline export, a named visible value changed
  from `FRESHNESS-OLD-<artifact>` to `FRESHNESS-NEW-<artifact>`, and a second
  export that differs, contains the new sentinel, and excludes the replaced old
  sentinel
- exact byte-for-byte equality between the attempted export string and the
  clipboard or fallback text for that invocation
- duplicate identifier preservation and issue reporting for applicable entity
  types
- empty text and empty collection representation
- multiline Unicode and special-character round-trip using values that include
  quotes, backticks, pipes, slash, backslash, tab, and newline
- multiple simultaneous issue ordering by entity order, declared field order, and
  condition order
- superseded copy attempts in both directions: older delayed success settling
  after newer failure and older delayed failure settling after newer success

`concept-explainer` additionally has rows for visible min/max control feedback on
add/remove and slider limits. `triage-board` additionally has rows for
empty-column and filtered-no-result feedback.

All seven artifacts include manifest parity rows. Reader artifacts record
producer-only data-integrity cases as `not_applicable` only with
`dataIntegrityObservation.notApplicableReason`.

Reader artifacts record producer-only clipboard recovery cases as
`not_applicable` only with `errorHandlingObservation.notApplicableReason`.

`feature-flags` data-integrity rows additionally cover duplicate group IDs,
duplicate flag keys, invalid rollout text, invalid or unavailable dependency
text, `null` normalized values with exact raw text in issues, and empty
groups/flags.

`prompt-tuner` data-integrity rows additionally cover duplicate slots, duplicate
sample IDs, empty template/slots/samples/fields/previews, raw invalid slot text,
first-occurrence field-key ordering, and multiline/special-character template,
field, and preview values.

`triage-board` data-integrity rows additionally cover duplicate ticket IDs across
columns, empty columns, all-empty board, current visible ticket order,
multiline/special-character ticket fields, and exact `## Issues` ordering.

For every structured export, UAT extracts the sole JSON fence, parses it, and
requires byte equality between the extracted JSON and
`JSON.stringify(value, null, 2)` applied to the parsed value.

The Markdown summary reports totals and identifies the exact source commit
represented by the JSON rows.
