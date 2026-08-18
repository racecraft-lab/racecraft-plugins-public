# Contract: Gallery Artifact

## Scope

This contract applies to the six new ART-004 gallery artifacts and the three existing artifacts repaired for horizontal keyboard scrolling.

## Slice Assignment

- Slice 1 repairs `code-approaches`, `implementation-plan`, and `module-map`.
- Slice 2 adds `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
- Slice 3 adds `visual-designs` and `component-variants`.

## Single-File Contract

- Each new artifact is one HTML file under `speckit-pro/artifact-gallery/templates/`.
- Each artifact embeds all CSS, JavaScript, data, SVG, and UI content needed to run.
- No build step, framework, package dependency, sibling asset, or network access is required.
- Optional typeface fallback is allowed when offline.
- Typeface fallback uses the canonical brand-kit stacks through their system and
  generic families, keeps text and controls readable, and does not use icon
  fonts or private-use glyphs as the only visible carrier of meaning.
- Canonical `BRAND-KIT` and `GALLERY-HEAD` regions are copied byte for byte.

## Attribution Contract

Each new artifact carries the exact five-label attribution header and names the upstream repository, pinned commit, source file, target Racecraft port, and self-contained derivative contract.

## Manifest Contract

- Exactly six manifest rows change `status` from `planned` to `shipped`.
- Slice 2 owns the four read-only status flips.
- Slice 3 owns the two decision-artifact status flips.
- No manifest identifier, category, title, stage, trigger, source filename, `when_to_use`, signal vocabulary, or `exports` value changes.
- Missing rows, extra rows, non-status field changes, and any status-flip count
  other than exactly six are blocking manifest drift.
- A row whose `exports` value is `[]` is read-only: its artifact exposes no prompt, Markdown, copy, download, disabled export-looking controls, or other export affordance.
- If a pinned upstream source includes export/download controls for read-only content, the port preserves the content, captions, and visible context but omits the controls rather than rendering disabled placeholders.

## Fill-Region Contract

| Artifact | Slice | Regions |
|---|---:|---|
| `visual-designs` | 3 | `feature-header`, `design-brief`, `background-toggle`, `directions` |
| `design-system` | 2 | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` |
| `component-variants` | 3 | `feature-header`, `variant-controls`, `variants`, `snippet-preview` |
| `animation-prototype` | 2 | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` |
| `interaction-prototype` | 2 | `feature-header`, `views`, `interaction-notes`, `open-questions` |
| `svg-illustrations` | 2 | `feature-header`, `illustrations`, `palette-rules` |

## Review Contract

Per-port validation checks file presence, attribution, canonical blocks, fill
regions, export declaration, and offline constraints. Shared manifest, test,
payload, proof, and generated-doc integration is serialized by slice. Validation
blocks on stale, missing, extra, truncated, rewritten, or byte-mismatched
generated outputs.

## Accessibility Contract

- Every interactive control in the six new artifacts and three repaired
  artifacts is reachable and operable by keyboard, shows visible focus, avoids
  keyboard traps, follows logical source-order focus, and uses no positive
  `tabindex`.
- Controls and custom control groups expose programmatic names, roles, states,
  and values where applicable. Reader-entered or reader-chosen data has visible
  labels or instructions.
- Declared horizontal-scroll regions are named groups with `tabindex="0"` and
  remain reachable in Safari keyboard navigation through Tab or Option-Tab,
  matching the active Safari setting recorded in UAT.
- Export status, copy success, invalid input, clipboard refusal, fallback
  reveal, and stale-attempt suppression use the Decision Export live-status
  contract.
- Light and dark themes use audited brand-kit WCAG AA pairings or measured
  equivalents for normal text, large text, meaningful non-text controls,
  focus indicators, status/error text, and SVG/palette annotations.
- Color is not the only carrier of selected, active, invalid,
  disabled/loading, drag insertion, SVG/palette, or theme/background meaning.
- Reduced-motion preference removes or replaces template-added animation,
  transitions, smooth scrolling, and motion-like feedback while preserving
  visible state and control meaning.

## State UX Contract

- Stateful artifacts expose current state in visible text, selected control state,
  or changed content.
- `component-variants` reset returns padding to `20px`, border to `hairline`,
  shadow to `shown`, clears transient hover-only emphasis, and refreshes the
  live card/snippet/export context.
- `animation-prototype` resets task completion on a second task activation while
  preserving the selected easing choice.
- `interaction-prototype` reset returns retained views to their initial order;
  any active dragging row or insertion indicator is removed during cleanup.
