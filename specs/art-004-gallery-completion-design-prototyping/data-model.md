# Data Model: ART-004 Gallery Completion - Design & Prototyping

## Entity: Gallery Artifact

**Fields**:

- `id`: stable identifier in `manifest.json`.
- `title`: reader-facing artifact title.
- `category`: existing manifest category.
- `stage`: `ad-hoc` for all six new ART-004 ports.
- `trigger`: existing manifest trigger; unchanged.
- `source.origin`: `upstream` for all six new ports.
- `source.file`: pinned upstream filename.
- `status`: changes from `planned` to `shipped` for exactly six ART-004 entries.
- `exports`: existing export declaration; unchanged.
- `template_file`: self-contained HTML page under `speckit-pro/artifact-gallery/templates/`.

**Validation rules**:

- The six ART-004 rows change only `status`.
- Each `source.file` matches the required pinned upstream source.
- Each shipped artifact file exists, opens without sibling resources, and carries the required attribution, `BRAND-KIT`, and `GALLERY-HEAD` regions.

**State transitions**:

- `planned -> shipped` for `visual-designs`, `design-system`, `component-variants`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- No transition for existing shipped artifacts; they receive only the horizontal-scroll repair.

## Entity: Pinned Upstream Source

**Fields**:

- `commit`: `58c305be97f47b26b678f2c07dec01d4242268ec`.
- `file`: upstream filename.
- `artifact_id`: target gallery artifact.
- `line_evidence`: required planning line count and local `wc -l` observation.

**Validation rules**:

- Every new artifact records the exact upstream source filename in the attribution header and manifest row.
- Source blobs are read-only evidence; upstream originals are not vendored into the repository.

## Entity: Fill Region

**Fields**:

- `artifact_id`: target artifact.
- `region`: source-of-truth fill-region key.
- `source_document`: `spec.md` for `feature-header`; `design-concept.md` for all other regions.

**Validation rules**:

- Each required region appears in the corresponding artifact.
- Only approved repeated sample groups may be compacted.
- Load-bearing selectors named in the spec remain present or are intentionally translated with equivalent behavior.

## Entity: Design Decision Export

**Fields**:

- `artifact_title`
- `feature_id`
- `feature_name`
- `format`: `prompt` or `markdown`.
- `selected_slot`: visual direction or base component variant.
- `selected_label`
- `anchor`
- `live_context_lines`
- `rationale`
- `fallback_payload`

**Validation rules**:

- Only `visual-designs` and `component-variants` expose export controls.
- A valid export requires one persistent radio selection and non-whitespace rationale.
- Invalid attempts announce the missing input, focus the first missing control, set `aria-invalid` only for blank rationale, and do not call clipboard APIs.
- Clipboard refusal reveals and focuses a textarea containing the same live payload.
- Delayed clipboard outcomes cannot overwrite newer status or fallback state.

**State transitions**:

- Empty -> incomplete attempt -> accessible status message.
- Empty -> selected and rationale supplied -> copy attempt.
- Copy attempt -> success status.
- Copy attempt -> refusal fallback with focused selectable payload.

## Entity: Horizontal Overflow Region

**Fields**:

- `artifact_id`
- `element`
- `data-rc-keyboard-scroll`
- `tabindex`
- `role`
- `aria-label`
- `scroll_position`

**Validation rules**:

- Every intentional horizontal overflow region has `data-rc-keyboard-scroll="horizontal"`.
- Every declared region has `tabindex="0"`, `role="group"`, and a trimmed, artifact-specific `aria-label`.
- The guard rejects artifacts with horizontal overflow styling but no declared keyboard-scroll regions.
- The negative fixture omits `tabindex` and must fail.

## Entity: Reviewability Budget

**Fields**:

- `primary_surface`
- `secondary_surfaces`
- `projected_reviewable_loc`
- `production_files`
- `total_authored_files`
- `generated_files`
- `status`
- `blockers`
- `split_decision`

**Validation rules**:

- The combined slice is blocked when projected reviewable LOC exceeds 800 or production files exceed 8.
- Generated files are declared separately and never treated as authored source.
- If blocked, the binding decision is "Stop and split"; implementation, Checklist, and Tasks do not proceed from this plan.

