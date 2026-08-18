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
- `generated_drift_status`: clean, stale, missing, extra, truncated, rewritten,
  or byte-mismatched.

**Validation rules**:

- Slices execute in order.
- Shared manifest, test, payload, proof, and generated-doc paths are serial and not parallel-safe.
- A slice with `gate_status=block` stops the workflow before Checklist and Tasks.
- Stale, missing, extra, truncated, rewritten, or byte-mismatched generated
  outputs block slice completion until regenerated from authoritative source.

## Entity: Gallery Artifact

**Fields**:

- `id`, `title`, `category`, `stage`, `trigger`, `source`, `status`, `exports`.
- `template_file`: one self-contained HTML file under `speckit-pro/artifact-gallery/templates/`.
- `slice`: 2 for read-only ports, 3 for decision ports.
- `interactive_controls`: stateful and stateless controls exposed by the port,
  including selection, slider, linked-screen or reorder, copy, fallback, reset,
  theme, and horizontal-scroll controls.
- `accessibility_contract`: keyboard operation, visible focus, no keyboard trap,
  source-order focus, no positive `tabindex`, name/role/state/value semantics,
  visible labels or instructions, non-color meaning, reduced-motion behavior,
  and light/dark brand-kit contrast conformance.

**Validation rules**:

- Exactly six ART-004 rows transition from `planned` to `shipped`.
- Slice 2 flips `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- Slice 3 flips `visual-designs` and `component-variants`.
- No manifest field other than `status` changes for those six rows.
- Missing rows, extra rows, non-status field changes, and wrong status-flip
  counts are blocking manifest drift.
- Artifacts with `exports: []` expose no prompt, Markdown, copy, download, or disabled export-looking controls; upstream export controls are adaptation candidates, not retained controls.
- Stateful artifacts expose visible current state and an observable reset or cleanup outcome for each persisted in-page state.
- Every interactive control is reachable and operable by keyboard, shows a
  visible focus indicator, avoids traps, follows logical source-order focus, and
  does not use positive `tabindex`.
- Every control or custom control group has a programmatically determinable
  name, role, state, and value where applicable, with visible labels or
  instructions for reader-entered or reader-chosen data.
- Both themes use audited brand-kit WCAG AA pairings or measured equivalents;
  color is not the only carrier of meaning, and reduced-motion preference
  removes or replaces template-added motion without hiding current state.
- Typeface fallback uses canonical brand-kit system or generic font stacks, and
  no control, status, or artifact meaning depends only on icon-font or
  private-use glyph rendering.

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
- `clipboard_refusal_modes`: unavailable Clipboard API, missing or non-callable
  `writeText`, synchronous exception, rejected write promise, denied permission,
  and local-file security restriction.
- `fallback_currentness`: current, stale-hidden, or absent.
- `status_role`: `role="status"` on `#export-status`.
- `status_live`: polite live announcement behavior for invalid input, copy
  success, clipboard refusal, fallback reveal, and stale-attempt suppression.
- `status_atomic`: `aria-atomic="true"` on `#export-status`.
- `fallback_label`: visible or programmatic label for `#fallback-field`.
- `focus_target`: first missing control on invalid attempts, fallback textarea
  on clipboard refusal, and unchanged current control for advisory status text.
- `invalid_state`: `aria-invalid="true"` only while the rationale is blank.

**Validation rules**:

- Only `visual-designs` and `component-variants` expose export controls.
- A valid export requires one persistent radio selection and non-whitespace rationale.
- Invalid attempts do not call clipboard APIs or reveal fallback text.
- Invalid attempts after a revealed fallback hide `#fallback`, clear
  `#fallback-field`, and leave focus unchanged before announcing validation.
- Clipboard refusal reveals and focuses the same live payload in a textarea.
- Every clipboard refusal mode uses the same fallback path without retrying or
  reporting success.
- An invocation counter prevents stale copy results from overwriting newer feedback.
- Export payloads read current visible state after reset as well as after manual state changes.
- Export-bearing input changes and resets invalidate any visible fallback by
  hiding it and clearing the field before a new status can describe changed
  state.
- `#export-status` is a polite atomic live status region and is not focused when
  copy, invalid-input, fallback, or stale-attempt status text changes.
- Fallback reveal is the only status path that intentionally moves focus after a
  copy attempt, and the focused textarea contains the same live payload.

## Entity: Horizontal Overflow Region

**Fields**:

- `artifact_id`, `element`, `data-rc-keyboard-scroll`, `tabindex`, `role`, `aria-label`, `scroll_position`.
- `source_order_index`: order recorded by the guard for manual focus-sequence
  confirmation.
- `positive_tabindex_absent`: true when no positive `tabindex` is used in the
  shipped artifact.
- `focus_visible`: true when keyboard focus exposes the canonical brand-kit
  focus indicator.
- `safari_key_path`: `Tab` or `Option-Tab`, matching the active Safari keyboard
  navigation setting used during UAT.

**Validation rules**:

- Every intentional horizontal overflow region has `data-rc-keyboard-scroll="horizontal"`.
- Every declared region has `tabindex="0"`, `role="group"`, and a specific non-empty `aria-label`.
- Slice 1 repairs the five existing affected regions before later slices add new regions.
- The global guard rejects positive `tabindex` values in shipped gallery
  artifacts and records artifact ID, source-order index, and accessible name for
  every declared region.
- Manual Safari UAT reaches every declared region through the active Tab or
  Option-Tab path, verifies visible focus, and confirms arrow-key scrolling
  without a keyboard trap.

## Entity: Accessibility Presentation

**Fields**:

- `artifact_id`.
- `theme`: light or dark.
- `token_pairing`: canonical brand-kit foreground, background, border, focus,
  status/error, and SVG/palette pairings used by the artifact.
- `contrast_floor`: 4.5:1 for normal text and 3:1 for large text or meaningful
  non-text indicators.
- `non_color_cue`: text, shape, icon, border, pattern, position, or state
  attribute that conveys selected, active, invalid, disabled/loading, drag
  insertion, SVG/palette, and theme/background meaning without color alone.
- `reduced_motion_behavior`: replacement or removal behavior for
  template-added animation, transitions, smooth scrolling, and motion-like
  feedback.

**Validation rules**:

- Each ART-004 artifact passes the light-theme and dark-theme contrast floors
  using audited brand-kit pairings or measured equivalents.
- Focus indicators, control borders, status/error text, and meaningful SVG
  annotations meet the non-text contrast floor.
- Reduced-motion preference leaves the same current state, reset outcome, and
  control meaning observable without template-added motion.
