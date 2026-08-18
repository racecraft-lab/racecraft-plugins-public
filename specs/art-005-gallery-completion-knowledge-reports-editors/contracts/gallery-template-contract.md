# Contract: Gallery Template

This contract applies to all seven ART-005 artifact files.

## Single-File Runtime

Each artifact is one HTML file under:

```text
speckit-pro/artifact-gallery/templates/<id>.html
```

Runtime requirements:

- no build step
- no bundler
- no preprocessor
- no sibling asset
- no server requirement
- no content or control dependency on network access
- opens directly over `file://`

## Canonical Blocks

Every shipped artifact embeds the canonical regions exactly once:

- `<!-- GALLERY-HEAD:START -->` through `<!-- GALLERY-HEAD:END -->` from
  `speckit-pro/artifact-gallery/theme-toggle.html`
- `/* BRAND-KIT:START */` through `/* BRAND-KIT:END */` from
  `speckit-pro/artifact-gallery/brand-kit.css`

The blocks are copied byte-for-byte. ART-005 does not edit the canonical source
files.

## Attribution Header

Every ART-005 artifact uses `source.origin: upstream` and therefore carries an
HTML comment near the top with:

- `Upstream repository: anthropics/html-effectiveness`
- `Upstream file: <manifest source.file>`
- `License: MIT`
- `License text: UPSTREAM-NOTICE.md`
- `Modified derivative: yes`
- `Copyright (c) 2026 Anthropic PBC`

The upstream file named in the header must match the manifest row exactly.

## Fill Inventory

The inventory comment appears immediately after the attribution header. Every
line uses:

```text
Slot: <slot-name> | Fills: <description> | Source: <source-artifact>
```

Slot names are filename-safe kebab-case. Marker pairs are flat and use:

```html
<!-- FILL:<slot-name>:START -->
...
<!-- FILL:<slot-name>:END -->
```

Required floors:

| Artifact | Required slots | List slots |
|---|---|---|
| `slide-deck` | `deck-title`, `slides`, `speaker-notes` | `slides` |
| `concept-explainer` | `concept-title`, `principles`, `worked-example`, `simulation-scenarios` | `simulation-scenarios` |
| `status-report` | `summary`, `landed`, `in-flight`, `blocked`, `next-actions` | `landed`, `in-flight`, `blocked`, `next-actions` |
| `incident-report` | `summary`, `timeline`, `impact`, `root-cause`, `follow-ups` | `timeline`, `follow-ups` |
| `triage-board` | `triage-items`, `column-labels` | `triage-items` |
| `feature-flags` | `flags`, `environment-notes` | `flags` |
| `prompt-tuner` | `prompt-variants`, `evaluation-notes` | `prompt-variants` |

Every list slot has at least two anchored top-level items using
`<slot-name>-<item-slug>`.

## Accessibility And Security

Each artifact:

- keeps visible focus on every control
- gives each control an accessible name
- makes every meaningful horizontal scroll region keyboard-focusable and named by
  placing `tabindex="0"` plus `role="group"` or equivalent grouping semantics and
  a non-empty `aria-label` or `aria-labelledby` on the actual scrolling element
- uses no positive `tabindex`
- reports dynamic success, failure, warning, dependency, movement, filter,
  validation, and editor-state messages through text plus `role="status"` or an
  equivalent live-region semantic
- respects reduced motion with no required animation, transition, or smooth
  scrolling
- uses text, shape, pattern, labels, or position so color is never the only
  carrier of meaning
- uses audited Racecraft token pairings for text, controls, focus indicators, and
  meaningful non-text indicators, or records explicit light/dark contrast
  evidence for any locally introduced color pairing; `--rc-border-subtle` remains
  decorative only and cannot carry meaning by itself
- carries no prohibited construct from `SPA-CONTRACT.md`, including `base`,
  scheme-relative resource URLs, `on*` handler attributes, `srcdoc`,
  target-bearing forms, or `ping`

## UX Boundary And Responsive States

Each artifact:

- remains readable and operable at a 360 CSS px mobile review width and a desktop
  review width of at least 1280 CSS px
- has no page-level horizontal overflow, clipped text, or overlapping text at
  those review widths
- permits horizontal scrolling only inside named, meaningful regions that satisfy
  the actual-scroll-element accessibility contract above

User-changeable surfaces also expose visible feedback for applicable boundary
states:

- `concept-explainer` shows current node/key counts plus min/max control limits;
  add/remove or slider actions at a limit leave state unchanged and update helper
  or status text
- `triage-board` shows explicit empty-column text and filtered-no-result text
- `feature-flags` shows dependency, invalid, empty, or unavailable normalized
  values beside the affected flag, group, or preview
- `prompt-tuner` shows empty template, slot, sample, and preview values as
  intentional empty strings and surfaces duplicate or invalid slot issues visibly

## Artifact-Specific Accessibility

`slide-deck`:

- exposes slide navigation as a named navigation group
- provides named previous/next controls or named direct-slide controls
- exposes current position text such as `Slide X of Y`
- has no auto-rotation
- keeps focus on the invoked control after control-driven slide changes
- moves focus to the active slide's named heading or container after a
  non-control slide change
- keeps hidden slides out of sequential focus order and the accessibility tree

`status-report` and `incident-report`:

- structure report sections with headings and lists for status, impact, blockers,
  timeline, remediation, and follow-up information
- express status, priority, error, and blocker meaning in text or another
  non-color cue

`triage-board`:

- exposes the board, columns, tickets, filters, reset, and export affordances with
  programmatic names
- provides keyboard-operable ticket movement between columns and reordering within
  a column for any pointer drag/drop movement preserved from upstream
- expresses priority and filter state in text or another non-color cue
- keeps focus on the moved ticket or movement control after a move
- announces resulting column, position, and filter state through the status region

`feature-flags`:

- groups related flags with programmatic group names
- names every flag control and exposes enabled, disabled, dependency, and issue
  state without relying on color alone
- associates dependency warning text with the relevant flag control or group

`prompt-tuner`:

- labels the editor, sample controls, slot fields, derived preview, reset, and
  export affordances
- preserves keyboard traversal through multiline and Unicode sample content

## Reader Versus Producer

Readers:

- `slide-deck`
- `concept-explainer`
- `status-report`
- `incident-report`

Readers carry no export control and keep `exports: []`.

Producers:

- `triage-board`
- `feature-flags`
- `prompt-tuner`

Producers implement the editor export contract and keep `exports:
["markdown"]`.
