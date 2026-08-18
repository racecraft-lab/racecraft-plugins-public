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
- `uatRows`: related `UATEvidenceRow` records

Validation rules:

- `templatePath` exists if and only if `status` is `shipped`.
- A reader has no export control and `exports: []`.
- A producer has exactly one `Copy as Markdown` control and `exports:
  ["markdown"]`.
- Each artifact embeds canonical `GALLERY-HEAD` and `BRAND-KIT` blocks exactly
  once when shipped.
- Every upstream-origin artifact carries a matching attribution header.

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

Validation rules:

- State is initialized from representative sample data.
- State is not persisted in browser storage or URL.
- Reload resets editor content to the seed state.
- Export reads live state at invocation time.

## MarkdownExport

Represents the text produced by a producer artifact.

Fields:

- `artifactId`
- `kind`: `markdown`
- `schemaVersion`: present for structured JSON editors
- `generatedText`
- `sourceStateSnapshot`
- `issues`

Validation rules:

- `triage-board` serializes columns in `now`, `next`, `later`, `cut` order and
  tickets in visible order.
- `feature-flags` emits one fenced JSON block with ordered groups, flags, and
  fields.
- `prompt-tuner` emits one fenced JSON block with ordered slots, visible
  samples, fields, and live preview text.
- Empty text is `""`; empty collections are `[]`; absent optional JSON fields
  are `null`; duplicate entries are preserved with deterministic `issues[]`
  records.

## ClipboardAttempt

Represents one export invocation.

Fields:

- `artifactId`
- `exportText`
- `clipboardAvailable`
- `writeAttempted`
- `result`: `success` or `fallback`
- `statusMessage`
- `fallbackVisible`
- `fallbackFocused`

Validation rules:

- At most one `navigator.clipboard.writeText()` attempt happens per invocation.
- Success message is `Copied. Markdown is on the clipboard.`
- Failure message is `Copy failed. The Markdown export is available below for
  manual copy.`
- Failure, rejection, unavailability, and synchronous throw reveal and focus a
  labeled selectable textarea containing the exact attempted string.

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
- `verdict`: `pass`, `fail`, or `not_applicable`
- `date`
- `driver`

Validation rules:

- Every seven-artifact matrix check has a row.
- `not_applicable` includes an observation proving why the check does not apply.
- Editor rows distinguish real clipboard success from forced unavailable,
  rejected, and synchronous-throw fallback checks.
