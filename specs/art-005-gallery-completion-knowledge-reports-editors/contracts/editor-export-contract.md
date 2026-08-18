# Contract: Editor Markdown Exports

This contract applies to `triage-board`, `feature-flags`, and `prompt-tuner`.

## Shared Clipboard Protocol

Each editor has exactly one export control:

```text
Copy as Markdown
```

On invocation:

1. Clear any stale fallback state.
2. Generate the Markdown string once from live visible state.
3. If `navigator.clipboard.writeText` is available, attempt it exactly once.
4. On success, announce:

```text
Copied. Markdown is on the clipboard.
```

5. On unavailability, rejection, or synchronous throw, announce:

```text
Copy failed. The Markdown export is available below for manual copy.
```

6. Reveal a labeled selectable textarea containing the exact attempted string.
7. Move focus to that textarea.

Hidden `execCommand` copying, automatic download, import-back, persistent
editor content, URL state, and server storage are prohibited.

The forced-unavailable UAT probe uses:

```js
Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
```

`delete navigator.clipboard` is prohibited in tests because it can leave the
inherited accessor in place and produce a false pass.

## Triage Board Export

Columns serialize in this order:

1. `now`
2. `next`
3. `later`
4. `cut`

Tickets serialize in current visible order within each column.

Shape:

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
```

Rules:

- Empty columns use `- _No tickets._`.
- Field bodies escape Markdown deterministically.
- Continuation lines are indented.
- Multiline, Unicode, quotes, backticks, and pipes are preserved.

## Feature Flags Export

Shape:

````markdown
# Feature Flags Export
Artifact: feature-flags
Export kind: markdown

```json
{
  "schemaVersion": "artifact-gallery.feature-flags.export.v1",
  "artifactId": "feature-flags",
  "groups": [],
  "issues": []
}
```
````

Rules:

- The Markdown wrapper contains exactly one fenced JSON block.
- Groups stay in declared order.
- Flags stay in declared order within each group.
- Object fields stay in this order: `key`, `description`, `enabled`,
  `requires`, `rollout`.
- `requires` is a string or `null`.
- `rollout` is a number or `null`.
- Invalid or unavailable normalized values use `null` and add an `issues[]`
  entry while preserving the raw value.

## Prompt Tuner Export

Shape:

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
  "samples": [],
  "issues": []
}
```
````

Rules:

- The Markdown wrapper contains exactly one fenced JSON block.
- Slots stay in pinned order.
- Samples stay in visible order.
- Fields inside each sample stay in slot order.
- `preview` is the live derived value.
- Empty text is `""`; empty collections are `[]`; absent optional fields are
  `null`.
- Duplicate array entries remain in visible order and add deterministic
  `issues[]` entries instead of being deduplicated.
