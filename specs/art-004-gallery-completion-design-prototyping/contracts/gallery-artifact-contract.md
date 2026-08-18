# Contract: Gallery Artifact

## Scope

This contract applies to the six new ART-004 gallery artifacts and the three existing artifacts repaired for horizontal keyboard scrolling.

## Single-File Contract

- Each new artifact is one HTML file under `speckit-pro/artifact-gallery/templates/`.
- Each artifact embeds all CSS, JavaScript, data, SVG, and UI content needed to run.
- No build step, framework, package dependency, sibling asset, or network access is required.
- Optional typeface fallback is allowed when offline.
- Canonical `BRAND-KIT` and `GALLERY-HEAD` regions are copied byte for byte.

## Attribution Contract

Each new artifact carries the exact five-label attribution header and names:

- Repository: `anthropics/html-effectiveness`
- Commit: `58c305be97f47b26b678f2c07dec01d4242268ec`
- Source file: the artifact's pinned upstream filename
- Port: the target Racecraft gallery artifact id
- Contract: self-contained Racecraft gallery derivative

## Manifest Contract

- Exactly six manifest rows change `status` from `planned` to `shipped`.
- No manifest identifier, category, title, stage, trigger, source filename, `when_to_use`, signal vocabulary, or `exports` value changes.
- `visual-designs` and `component-variants` keep `exports: ["prompt", "markdown"]`.
- `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations` keep `exports: []`.

## Fill-Region Contract

The implementation preserves these required regions:

| Artifact | Regions |
|---|---|
| `visual-designs` | `feature-header`, `design-brief`, `background-toggle`, `directions` |
| `design-system` | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` |
| `component-variants` | `feature-header`, `variant-controls`, `variants`, `snippet-preview` |
| `animation-prototype` | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` |
| `interaction-prototype` | `feature-header`, `views`, `interaction-notes`, `open-questions` |
| `svg-illustrations` | `feature-header`, `illustrations`, `palette-rules` |

## Review Contract

- Per-port validation checks file presence, attribution, canonical blocks, fill regions, export declaration, and offline constraints.
- Shared manifest, test, payload, proof, and generated-doc integration is serialized.
- Generated outputs are regenerated from source and are never hand-edited.

