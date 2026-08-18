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
- makes every horizontal scroll region keyboard-focusable and named
- reports status as text, not color alone
- respects reduced motion with no required animation, transition, or smooth
  scrolling
- uses text, shape, pattern, labels, or position so color is never the only
  carrier of meaning
- carries no prohibited construct from `SPA-CONTRACT.md`, including `base`,
  scheme-relative resource URLs, `on*` handler attributes, `srcdoc`,
  target-bearing forms, or `ping`

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
