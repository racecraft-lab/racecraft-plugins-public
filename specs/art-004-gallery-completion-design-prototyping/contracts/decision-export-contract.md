# Contract: Decision Export

## Scope

This contract applies only to `visual-designs` and `component-variants`.

## Required Controls

- A keyboard-persistent radio group chooses exactly one design decision and
  exposes its name, role, checked state, and selected value.
- The visible copy controls are labelled `Copy as prompt` and `Copy as Markdown`.
- A labelled `#rationale-field` captures the reader's rationale.
- `#export-status` carries `role="status"`, `aria-live="polite"`, and
  `aria-atomic="true"`.
- `#fallback` contains labelled selectable `#fallback-field` text when
  clipboard access is refused.
- Every radio, rationale, copy, fallback, and reset control is keyboard
  operable, visibly focused, named, and in logical source-order focus sequence
  without positive `tabindex`.

## Payload Order

Both prompt and Markdown formats emit plain lines in this order:

1. `Artifact: <artifact title>`
2. `Feature: <feature id> <feature name>`
3. blank line
4. the format- and artifact-specific lead sentence
5. blank line
6. `<slot> / <selected visible label>  (#<anchor>)`
7. artifact live context lines
8. `Rationale: <trimmed reader rationale>`

## Visual Designs Context

Prompt lead:

`Implement the visual direction named below and no other. The value in parentheses is the anchor of the direction it names.`

Markdown lead:

`Visual direction chosen while reviewing these options.`

Live context lines:

- `Background: <light|dark>`
- `Direction note: <visible direction note>`

## Component Variants Context

Prompt lead:

`Implement the base component variant named below and no other. The value in parentheses is the anchor of the variant it names.`

Markdown lead:

`Base component variant chosen while reviewing these states.`

Live context lines:

1. `Variant note: <visible variant note>`
2. `States displayed: default, hover, focus, disabled, error, loading`
3. `Padding: <value>`
4. `Border: <value>`
5. `Shadow: <shown|hidden>`
6. `Snippet:`
7. the live snippet text

## Validation Behavior

- If both choice and rationale are absent, announce `Choose one option and enter a rationale before copying.`
- If only the visual direction is absent, announce `Choose one visual direction before copying.`
- If only the base variant is absent, announce `Choose one base variant before copying.`
- If only rationale is absent, announce `Enter a rationale before copying.`
- Invalid attempts focus the first missing control.
- Invalid attempts set `aria-invalid="true"` only on a blank rationale.
- Invalid attempts do not call the clipboard and do not reveal fallback text.
- Invalid attempts after a previously revealed fallback hide `#fallback`, clear
  `#fallback-field`, and leave focus unchanged before announcing the validation
  message.
- Before a valid attempt, stale fallback content is hidden.
- Successful copy updates `#export-status` without moving focus.
- On clipboard refusal, announce exactly `Copy failed. The text is in the field below. Select it and copy it by hand.`
- On clipboard refusal, write the same live payload into `#fallback-field`, reveal `#fallback`, and focus the textarea.
- Clipboard refusal covers unavailable `navigator.clipboard`, missing or
  non-callable `writeText`, synchronous exceptions, rejected write promises,
  denied permission, and local-file security restrictions; each case uses the
  same fallback path without retrying or reporting success.
- An invocation counter prevents older delayed copy results from overwriting newer status, focus, or fallback state.
- Status messages for invalid input, successful copy, clipboard refusal,
  fallback reveal, and stale-attempt suppression are exposed through the polite
  atomic `#export-status` region.
- Any export-bearing input change or reset after fallback reveal invalidates the
  visible fallback by hiding `#fallback` and clearing `#fallback-field`, so a
  stale payload cannot remain visible beside changed state.

## Accessibility Contract

- Visible labels or instructions identify every reader-entered or reader-chosen
  value before export.
- Color is not the only way to indicate selected, invalid, disabled/loading, or
  fallback-visible state.
- Light and dark theme treatments for copy controls, status/error text, focus
  indicators, and fallback fields use audited brand-kit WCAG AA pairings or
  measured equivalents.
- Reduced-motion preference removes or replaces template-added transitions or
  motion-like feedback without changing selected decision, rationale, fallback
  payload, or status meaning.
