# Contract: Editor Markdown Exports

This contract applies to `triage-board`, `feature-flags`, and `prompt-tuner`.

## Fresh Snapshot Protocol

Every `Copy as Markdown` invocation captures a fresh immutable snapshot of the
current visible editor state after the triggering UI change is applied. The
export string is generated exactly once from that snapshot and is the only string
used for clipboard writes, equality checks, or fallback display.

Editors MUST NOT precompute export text at page initialization, cache export text
across invocations, or regenerate different clipboard and fallback strings for
one attempt.

Before each snapshot, the editor clears the prior status text, hides the prior
fallback, and empties the prior fallback field. A later invocation supersedes
earlier unsettled copy attempts. If an older asynchronous success or failure
settles after a later invocation, it records no current UI effect and does not
change the later status, fallback contents, fallback visibility, or focus target.

## Shared Clipboard Protocol

Each editor has exactly one export control:

```text
Copy as Markdown
```

On invocation:

1. Clear any stale fallback state.
2. Generate the Markdown string once from live visible state.
3. Read `navigator.clipboard` for this invocation. If `writeText` is callable,
   attempt it exactly once; if the object or callable method is absent, make no
   write attempt and take the fallback path.
4. On success, announce:

```text
Copied. Markdown is on the clipboard.
```

5. On unavailability, a permission-denied rejection such as `NotAllowedError`,
   any other rejected promise, or synchronous throw, announce:

```text
Copy failed. The Markdown export is available below for manual copy.
```

6. Reveal a labeled selectable textarea containing the exact attempted string.
7. Move focus to that textarea.

The user-facing failure message is identical for all declared failure classes
and does not expose or guess browser exception details. A successful current
invocation leaves focus on its invoked export control and leaves the fallback
hidden and empty. A repeated current failure replaces the fallback value with
the latest invocation's exact attempted string; it never appends to or retains
an older export.

Both exact messages update the editor's persistent status region using
`role="status"` or an equivalent live-region semantic. The status region does
not become an extra tab stop and does not replace the focused manual-copy
textarea required for failure recovery.

Hidden `execCommand` copying, automatic download, import-back, persistent
editor content, URL state, and server storage are prohibited.

Each editor exposes applicable empty, invalid, dependency, unavailable-value, and
filtered-no-result states before export in visible text or inline cues. Dynamic
state changes update the same status-region mechanism used for copy feedback, and
the exported Markdown preserves the visible state exactly according to the
artifact-specific ordering and edge-value rules below.

The forced-unavailable UAT probe uses:

```js
Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
```

`delete navigator.clipboard` is prohibited in tests because it can leave the
inherited accessor in place and produce a false pass.

## Failure And Transition Matrix

Each producer is verified over direct `file://` for these current-invocation
cases:

| Case | Method shape | Write attempts | Required terminal state |
|---|---|---:|---|
| genuine success | callable, fulfills | 1 | success message; fallback hidden and empty; invoked-control focus unchanged |
| clipboard absent | clipboard object absent | 0 | failure message; exact fallback visible, selectable, and focused |
| method non-callable | `writeText` absent or not a function | 0 | failure message; exact fallback visible, selectable, and focused |
| permission denied | callable, rejects with permission denial | 1 | failure message; exact fallback visible, selectable, and focused |
| generic rejection | callable, rejects for another reason | 1 | failure message; exact fallback visible, selectable, and focused |
| synchronous throw | callable, throws before returning | 1 | failure message; exact fallback visible, selectable, and focused |

The sequential transition check runs failure, then success, then failure with
three distinct live-state sentinels. After each step, the exact status,
fallback visibility/content, and focused target match only that invocation.
The concurrency check covers both older-failure-after-newer-success and
older-success-after-newer-failure; an older settlement cannot mutate those four
current-state observations.

## Issue Record Schema

Structured editor `issues[]` entries and the `triage-board` issue appendix use
the same ordered fields:

1. `code`
2. `artifactId`
3. `entityType`
4. `entityId`
5. `field`
6. `occurrenceIndex`
7. `relatedOccurrenceIndex`
8. `rawValue`
9. `normalizedValue`
10. `message`

Field rules:

- `code`: one of `empty_required_value`, `invalid_value`,
  `unavailable_value`, or `duplicate_identifier`
- `artifactId`: one of `triage-board`, `feature-flags`, or `prompt-tuner`
- `entityType`: one of `artifact`, `feature_flag_group`, `feature_flag`,
  `prompt_slot`, `prompt_sample`, or `triage_ticket`
- `entityId`: string or `null`
- `field`: declared schema field name
- `occurrenceIndex`: one-based integer or `null`
- `relatedOccurrenceIndex`: one-based first-occurrence index for duplicates;
  otherwise `null`
- `rawValue`: exact original text, number, boolean, or `null` when no single raw
  input exists
- `normalizedValue`: string, number, boolean, or `null`
- `message`: one stable message from the table below

| Code | Message |
|---|---|
| `empty_required_value` | `Required value is empty.` |
| `invalid_value` | `Value is invalid and was not normalized.` |
| `unavailable_value` | `A normalized value is unavailable.` |
| `duplicate_identifier` | `Identifier duplicates the first visible occurrence.` |

Issue order is deterministic:

1. Traverse entities in export order.
2. Traverse fields in declared schema order.
3. Emit conditions in this order: `empty_required_value`, `invalid_value`,
   `unavailable_value`, `duplicate_identifier`.
4. For duplicates, leave every value in place and emit an issue for each
   occurrence after the first, with `relatedOccurrenceIndex` pointing to the first
   visible occurrence.
5. Never derive issue order from arbitrary object-key enumeration.

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
- Ticket fields serialize in this order: `id`, `title`, `tag`, `estimate`,
  `owner`.
- Field bodies escape Markdown deterministically.
- Continuation lines are indented.
- Multiline, Unicode, quotes, backticks, and pipes are preserved.
- Keyboard movement between columns and reordering within a column updates the
  same visible order that the export serializes.
- Movement status announces the ticket's resulting column and position while
  keeping focus on the moved ticket or its movement control.
- Duplicate ticket IDs are preserved across all columns and reported in issue
  records for every occurrence after the first.
- After the `Cut` section, append this fixed issue section:

```markdown
## Issues
- _No issues._
```

When issues exist, write one numbered item per issue in the deterministic order
above:

```markdown
## Issues
- Issue 1
  - Code: `duplicate_identifier`
  - Artifact: `triage-board`
  - Entity type: `triage_ticket`
  - Entity id: `"T-101"`
  - Field: `id`
  - Occurrence index: 3
  - Related occurrence index: 1
  - Raw value: `"T-101"`
  - Normalized value: `"T-101"`
  - Message: Identifier duplicates the first visible occurrence.
```

String and `null` scalar values in the issue appendix use JSON scalar
representation.

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
- Wrapper fields stay in this order: `schemaVersion`, `artifactId`, `groups`,
  `issues`.
- Group fields stay in this order: `id`, `label`, `flags`.
- Flag fields stay in this order: `key`, `description`, `enabled`, `requires`,
  `rollout`.
- Issue fields stay in the issue-record order above.
- Groups stay in declared order.
- Flags stay in declared order within each group.
- Group IDs, group labels, flag keys, and descriptions are strings.
- `enabled` is a boolean.
- `requires` is a string or `null`.
- `rollout` is a number or `null`.
- `groups`, `flags`, and `issues` are arrays.
- Duplicate group IDs and flag keys are preserved in declared/visible order and
  add `duplicate_identifier` issues for every occurrence after the first.
- Invalid rollout text and invalid or unavailable dependency text preserve the
  exact original text in `rawValue`; the exported normalized field and issue
  `normalizedValue` are `null`.
- Invalid or unavailable normalized values are not clamped, truncated, coerced,
  sanitized, deduplicated, or renamed.

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
- Wrapper fields stay in this order: `schemaVersion`, `artifactId`, `template`,
  `slots`, `samples`, `issues`.
- Sample fields stay in this order: `id`, `label`, `planClass`, `fields`,
  `preview`.
- Issue fields stay in the issue-record order above.
- Slots stay in pinned order.
- Samples stay in visible order.
- Fields inside each sample stay in first-occurrence slot order and include each
  distinct slot key once.
- `preview` is the live derived value.
- Empty text is `""`; empty collections are `[]`; absent optional fields are
  `null`.
- `template`, slot entries, sample IDs, labels, field values, and previews are
  strings.
- `planClass` is a string or `null`.
- `slots`, `samples`, and `issues` are arrays.
- Duplicate slot identifiers and sample IDs remain in visible/export order and
  add deterministic `duplicate_identifier` issues instead of being deduplicated
  or renamed.
- Raw invalid slot text is preserved exactly in `rawValue`; unavailable
  normalized values use `null`.
- Multiline text, Unicode, quotes, backticks, pipes, slash, backslash, tab,
  newline, and other special characters round-trip through the fenced JSON
  without data loss.
