# Data Model: ART-004 Gallery Completion - Design & Prototyping

## Entity: Implementation Slice

**Fields**:

- `number`: 1, 2, or 3.
- `name`: `keyboard-foundation`, `read-only-ports`, or `decision-ports`.
- `authored_operations`: exact new/modified source and test files.
- `generated_operations`: derived output paths regenerated from source.
- `gate_input`: durable contract file under `contracts/`.
- `reviewable_loc`, `production_files`, `total_files`.
- `gate_status`: `pass`, `warn`, or `block`.

**Validation rules**:

- Slices execute in order.
- Shared manifest, test, payload, proof, and generated-doc paths are serial and not parallel-safe.
- A slice with `gate_status=block` stops the workflow before Checklist and Tasks.

## Entity: Gallery Artifact

**Fields**:

- `id`, `title`, `category`, `stage`, `trigger`, `source`, `status`, `exports`.
- `template_file`: one self-contained HTML file under `speckit-pro/artifact-gallery/templates/`.
- `slice`: 2 for read-only ports, 3 for decision ports.

**Validation rules**:

- Exactly six ART-004 rows transition from `planned` to `shipped`.
- Slice 2 flips `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- Slice 3 flips `visual-designs` and `component-variants`.
- No manifest field other than `status` changes for those six rows.

## Entity: Pinned Upstream Source

**Fields**:

- `commit`: `58c305be97f47b26b678f2c07dec01d4242268ec`.
- `file`: upstream filename.
- `artifact_id`: target gallery artifact.
- `line_evidence`: required planning line count and local `wc -l` observation.

**Validation rules**:

- Each new artifact records the exact upstream source filename in its attribution and manifest row.
- Upstream originals are read-only evidence and are not vendored.

## Entity: Fill Region

**Fields**:

- `artifact_id`
- `region`
- `source_document`: `spec.md` for `feature-header`; `design-concept.md` for other regions.
- `list_slot`: true for `visual-designs.directions`, `component-variants.variants`, and `interaction-prototype.views`.

**Validation rules**:

- Each required region appears in the corresponding artifact.
- `test-artifact-fill-regions.py` is updated for ART-004 floor/list-slot coverage.
- Only approved repeated sample groups may be compacted.

## Entity: Design Decision Export

**Fields**:

- `artifact_title`, `feature_id`, `feature_name`, `format`, `selected_slot`, `selected_label`, `anchor`, `live_context_lines`, `rationale`, `fallback_payload`.

**Validation rules**:

- Only `visual-designs` and `component-variants` expose export controls.
- A valid export requires one persistent radio selection and non-whitespace rationale.
- Invalid attempts do not call clipboard APIs or reveal fallback text.
- Clipboard refusal reveals and focuses the same live payload in a textarea.
- An invocation counter prevents stale copy results from overwriting newer feedback.

## Entity: Horizontal Overflow Region

**Fields**:

- `artifact_id`, `element`, `data-rc-keyboard-scroll`, `tabindex`, `role`, `aria-label`, `scroll_position`.

**Validation rules**:

- Every intentional horizontal overflow region has `data-rc-keyboard-scroll="horizontal"`.
- Every declared region has `tabindex="0"`, `role="group"`, and a specific non-empty `aria-label`.
- Slice 1 repairs the five existing affected regions before later slices add new regions.

