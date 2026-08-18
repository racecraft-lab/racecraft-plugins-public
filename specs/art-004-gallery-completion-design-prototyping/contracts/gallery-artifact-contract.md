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
- Canonical `BRAND-KIT` and `GALLERY-HEAD` regions are copied byte for byte.

## Attribution Contract

Each new artifact carries the exact five-label attribution header and names the upstream repository, pinned commit, source file, target Racecraft port, and self-contained derivative contract.

## Manifest Contract

- Exactly six manifest rows change `status` from `planned` to `shipped`.
- Slice 2 owns the four read-only status flips.
- Slice 3 owns the two decision-artifact status flips.
- No manifest identifier, category, title, stage, trigger, source filename, `when_to_use`, signal vocabulary, or `exports` value changes.

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

Per-port validation checks file presence, attribution, canonical blocks, fill regions, export declaration, and offline constraints. Shared manifest, test, payload, proof, and generated-doc integration is serialized by slice.

