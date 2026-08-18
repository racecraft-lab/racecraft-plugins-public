# Contract: Decision Export

## Scope

This contract applies only to `visual-designs` and `component-variants`.

## Required Controls

- A keyboard-persistent radio group chooses exactly one design decision.
- The visible copy controls are labelled `Copy as prompt` and `Copy as Markdown`.
- A labelled `#rationale-field` captures the reader's rationale.
- `#export-status` carries `role="status"`.
- `#fallback` contains selectable `#fallback-field` text when clipboard access is refused.

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
- Before a valid attempt, stale fallback content is hidden.
- On clipboard refusal, announce exactly `Copy failed. The text is in the field below. Select it and copy it by hand.`
- On clipboard refusal, write the same live payload into `#fallback-field`, reveal `#fallback`, and focus the textarea.
- An invocation counter prevents older delayed copy results from overwriting newer status, focus, or fallback state.

