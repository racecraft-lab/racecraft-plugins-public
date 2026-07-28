# Data Model: Artifact Brand Kit & Gallery Foundation

**Feature**: ART-001 | **Date**: 2026-07-28

All paths in this document are relative to the repository root. Paths written
into `manifest.json` itself are relative to the manifest's own directory.

## Entity 1 — Routing Catalog (`manifest.json`)

Top-level object with **exactly three keys, in this order** (FR-007, Session 2):

| Key | Type | Value |
|-----|------|-------|
| `schema_version` | string | `"1.0"` |
| `signals` | array of string | The five vocabulary members, in FR-015 order |
| `templates` | array of object | 21 entries |

Nothing else is legal at top level — no `$schema` pointer, no `description`.

```json
{
  "schema_version": "1.0",
  "signals": [
    "competing_approaches",
    "brownfield_change",
    "self_review_findings",
    "large_diff",
    "operational_flow_change"
  ],
  "templates": [ /* 21 entries */ ]
}
```

## Entity 2 — Gallery Template Entry

**Exactly eight keys**, in FR-007's declaration order. No ninth key. **No stored
path** — the artifact resolves as `templates/<id>.html` relative to the
manifest's own directory (FR-007, FR-009).

| Key | Type | Rule |
|-----|------|------|
| `id` | string | kebab-case; unique across the catalog; equals the artifact file stem |
| `category` | string | one of the nine-member enum below |
| `title` | string | non-empty; names the document |
| `when_to_use` | string | non-empty guidance prose |
| `stage` | string | `draft-pr` \| `final-pr` \| `ad-hoc` |
| `trigger` | object | one of the two forms below |
| `source` | object | one of the two forms below |
| `status` | string | `planned` \| `shipped` |

### Category enum (nine members)

Adopted verbatim from the upstream gallery's own index taxonomy, kebab-cased.
Every one of the 20 ported entries **inherits** its upstream group — no category
is invented for a ported entry.

| Enum member | Upstream index heading |
|-------------|------------------------|
| `exploration-planning` | "Exploration & Planning" |
| `code-review` | "Code Review & Understanding" |
| `design` | "Design" |
| `prototyping` | "Prototyping" |
| `diagrams` | "Illustrations & Diagrams" |
| `decks` | "Decks" |
| `research` | "Research & Learning" |
| `reports` | "Reports" |
| `editors` | "Custom Editing Interfaces" |

`uat-walkthrough` (repository-authored) takes `editors`; no tenth member is
minted (Session 2).

### Trigger — two forms only (FR-008, FR-016)

```json
{ "always": true }
```

```json
{ "any_of": ["competing_approaches"] }
```

- `any_of` MUST be non-empty. An empty array is a hard validation failure — that
  is what makes deleting the last signal fail loudly instead of silently
  disabling routing.
- No nesting, no conjunction, no negation, no third form.
- The trigger field is mandatory on **every** entry including `ad-hoc` ones, so
  all 21 entries carry one uniform validated shape. Ad-hoc triggers are never
  evaluated, because the stage filter runs first and excludes them.

### Source — two forms, discriminated by `origin` (FR-020)

```json
{ "origin": "upstream", "file": "16-implementation-plan.html" }
```

```json
{ "origin": "repository" }
```

`file` carries the **exact** upstream filename so the numeric prefix survives.
The upstream repository is named once in `SPA-CONTRACT.md`, not repeated across
20 entries. `origin` is the discriminator that makes the FR-020 attribution
check mechanical: an `upstream` entry's artifact must carry the attribution
header; a `repository` entry's artifact must not carry an upstream copyright
line.

## Entity 3 — Routing Signal Vocabulary (five members)

Declared as data under the top-level `signals` key, which is the single
authority for membership (FR-017). Meanings live in `SPA-CONTRACT.md`.

| Signal | Meaning | Consuming entry |
|--------|---------|-----------------|
| `competing_approaches` | Planning weighed more than one viable implementation approach | `code-approaches` |
| `brownfield_change` | The change modifies existing code rather than adding only new files | `module-map` |
| `self_review_findings` | The pre-PR self-review recorded at least one gap | `annotated-diff` |
| `large_diff` | The finished change's size reached the repository's existing warn or block threshold | `annotated-diff` |
| `operational_flow_change` | The change alters a documented multi-step runtime or delivery process | `flowchart` |

Closure holds in **both** directions: no entry names a signal outside this set,
and every member is consumed by at least one entry.

## Seeded catalog — all 21 entries

Stage/trigger assignments are fixed by Clarifications Session 1: 4 staged
always-applies, 4 staged conditional, 13 ad-hoc always-applies.

| # | `id` | `category` | `stage` | `trigger` | `source.origin` | `source.file` | Ships in |
|---|------|-----------|---------|-----------|------------------|----------------|----------|
| 1 | `implementation-plan` | `exploration-planning` | `draft-pr` | always | upstream | `16-implementation-plan.html` | ART-002 |
| 2 | `spec-explainer` | `research` | `draft-pr` | always | upstream | `14-research-feature-explainer.html` | ART-002 |
| 3 | `code-approaches` | `exploration-planning` | `draft-pr` | any_of `competing_approaches` | upstream | `01-exploration-code-approaches.html` | ART-002 |
| 4 | `module-map` | `code-review` | `draft-pr` | any_of `brownfield_change` | upstream | `04-code-understanding.html` | ART-002 |
| 5 | `pr-writeup` | `code-review` | `final-pr` | always | upstream | `17-pr-writeup.html` | ART-003 |
| 6 | `annotated-diff` | `code-review` | `final-pr` | any_of `self_review_findings`, `large_diff` | upstream | `03-code-review-pr.html` | ART-003 |
| 7 | `flowchart` | `diagrams` | `final-pr` | any_of `operational_flow_change` | upstream | `13-flowchart-diagram.html` | ART-003 |
| 8 | `uat-walkthrough` | `editors` | `final-pr` | always | repository | — | ART-009 |
| 9 | `visual-designs` | `exploration-planning` | `ad-hoc` | always | upstream | `02-exploration-visual-designs.html` | ART-004 |
| 10 | `design-system` | `design` | `ad-hoc` | always | upstream | `05-design-system.html` | ART-004 |
| 11 | `component-variants` | `design` | `ad-hoc` | always | upstream | `06-component-variants.html` | ART-004 |
| 12 | `animation-prototype` | `prototyping` | `ad-hoc` | always | upstream | `07-prototype-animation.html` | ART-004 |
| 13 | `interaction-prototype` | `prototyping` | `ad-hoc` | always | upstream | `08-prototype-interaction.html` | ART-004 |
| 14 | `svg-illustrations` | `diagrams` | `ad-hoc` | always | upstream | `10-svg-illustrations.html` | ART-004 |
| 15 | `slide-deck` | `decks` | `ad-hoc` | always | upstream | `09-slide-deck.html` | ART-005 |
| 16 | `concept-explainer` | `research` | `ad-hoc` | always | upstream | `15-research-concept-explainer.html` | ART-005 |
| 17 | `status-report` | `reports` | `ad-hoc` | always | upstream | `11-status-report.html` | ART-005 |
| 18 | `incident-report` | `reports` | `ad-hoc` | always | upstream | `12-incident-report.html` | ART-005 |
| 19 | `triage-board` | `editors` | `ad-hoc` | always | upstream | `18-editor-triage-board.html` | ART-005 |
| 20 | `feature-flags` | `editors` | `ad-hoc` | always | upstream | `19-editor-feature-flags.html` | ART-005 |
| 21 | `prompt-tuner` | `editors` | `ad-hoc` | always | upstream | `20-editor-prompt-tuner.html` | ART-005 |

**All 21 entries ship with `status: "planned"`.** ART-001 ports no template, so
no artifact file exists yet and no existence check fires. Each port spec flips
exactly one value from `planned` to `shipped` (SC-004).

Counts that must hold, and do:

- 21 entries total; 20 `origin: upstream` + 1 `origin: repository`
- 4 `draft-pr` + 4 `final-pr` + 13 `ad-hoc`
- 4 staged always-applies (#1, #2, #5, #8) + 4 staged conditional (#3, #4, #6, #7)
- upstream split 4 draft-PR / 3 final-PR / 6 design-and-prototyping / 7
  knowledge-report-editor, matching FR-007
- every one of the five signals consumed at least once

## Entity 4 — Brand Token Set (`brand-kit.css`)

Canonical file delimited by `/* BRAND-KIT:START */` … `/* BRAND-KIT:END */`.
Everything inside the markers is embedded verbatim into each artifact's
`<style>`. Above the start marker sits the provenance header (FR-012) and the
audited contrast table; those are **outside** the compared region so the header
can carry file-specific commentary without breaking the byte-compare.

Token families inside the block:

- `--rc-surface`, `--rc-surface-raised`, `--rc-surface-sunken`,
  `--rc-surface-muted` — the 70% warm-neutral dominant family
- `--rc-border-subtle` (decorative), `--rc-border-strong` (meaningful non-text,
  audited to 3:1)
- `--rc-text`, `--rc-text-muted`, `--rc-link`
- `--rc-accent` (20% blue, large-text and non-text only),
  `--rc-brand-red` (10% punctuation-level emphasis, non-text and large text),
  `--rc-danger-text` (the AA-body-safe red for red body copy)
- `--rc-font-display`, `--rc-font-body`, `--rc-font-mono` — brand face first,
  system fallback after
- focus-visible treatment and reduced-motion handling

Dark values are supplied under `@media (prefers-color-scheme: dark)` and under
`:root[data-theme="dark"]`, with `:root[data-theme="light"]` forcing light back
on. `color-scheme: light dark` is declared so form controls and scrollbars
follow.

### Audited AA contrast pairings

Computed with the WCAG 2.x relative-luminance formula, per theme independently
(FR-005, SC-007). Ratios are stated in the `brand-kit.css` comment block so a
template port can verify a pairing without re-deriving it.

**Light theme** — surfaces `#F7F6F4` / `#FFFFFF` / `#F1F0EC` / `#E8E5DF`

| Foreground | Ratio range across the four surfaces | Verdict |
|------------|--------------------------------------|---------|
| `--rc-text` `#111827` | 14.11 – 17.74 | AA body |
| `--rc-text-muted` `#4B5563` | 6.01 – 7.56 | AA body |
| `--rc-link` `#2A6A99` | 4.61 – 5.80 | AA body |
| `--rc-accent` `#3C89C6` | 3.30 – 3.76 on surface/raised/sunken | AA large + non-text |
| `--rc-brand-red` `#dc143c` | 3.97 – 4.99 | AA large + non-text |
| `--rc-danger-text` `#C4102F` | 4.82 – 6.05 | AA body |
| `--rc-border-strong` `#8A8578` | 3.41 on `--rc-surface` | AA non-text |

**Dark theme** — surfaces `#1A1A1A` / `#1F2937` / `#141414` / `#1E1E1E`

| Foreground | Ratio range across the four surfaces | Verdict |
|------------|--------------------------------------|---------|
| `--rc-text` `#E6E6E6` | 11.76 – 14.76 | AA body |
| `--rc-text-muted` `#9CA3AF` | 5.78 – 7.26 | AA body |
| `--rc-link` `#7CB3DD` | 6.54 – 8.20 | AA body |
| `--rc-accent` `#3C89C6` | 3.90 – 4.90 | AA large + non-text |
| `--rc-danger-text` `#FF6B85` | 5.38 – 6.75 | AA body |
| `--rc-border-strong` `#6B7280` | 3.60 on `--rc-surface` | AA non-text |

Two constraints fall out of the audit and are recorded as rules in the CSS
comment, because they are the only pairings that do not pass:

1. **`--rc-accent` is never paired with `--rc-surface-muted` in light theme** —
   `#3C89C6` on `#E8E5DF` measures 2.99, just under the 3:1 non-text floor. Use
   `--rc-link` there instead.
2. **`--rc-border-subtle` is decorative only** — 1.24 (light) and 1.69 (dark)
   against their surfaces. Any boundary that conveys meaning (form control
   edges, focus ring) MUST use `--rc-border-strong`.

Focus ring uses `--rc-link` in both themes: 5.37 light, 7.75 dark.

## Entity 5 — Theme Toggle Snippet (`theme-toggle.html`)

Canonical file delimited by `<!-- THEME-TOGGLE:START -->` …
`<!-- THEME-TOGGLE:END -->`, byte-compared by the same mechanism as the CSS
block (FR-003, FR-006).

Contains the control markup plus the inline behavior:

- Reads a stored override, falling back to the OS signal.
- Applies `data-theme` to `:root` **before first paint**, so a dark-OS reviewer
  sees no light flash (FR-004, SC-005).
- Writes the override inside `try` / `catch`; when a browser refuses storage for
  `file://` documents the override still applies for the session and nothing is
  reported as an error (FR-004, Story 3 scenario 3).

## Entity 6 — Provenance Record

Lives in the `brand-kit.css` header, above the start marker (FR-012):

- `racecraft-lab/racecraft` `docs/brand/*` at commit
  `30237cceaeb398e9fc08d8570714f24ff661c867`, captured 2026-07-04 — cited by
  repository name, path, SHA, and date only. **No prose reproduced.**
- `docs-site/src/styles/brand.css` — the public in-repo token source the palette
  is reconciled against.

No automated cross-repository comparison exists; re-sync is a deliberate human
edit.

## Entity 7 — Upstream Permission Notice

One file reproducing the upstream MIT permission notice verbatim (FR-020),
which every ported artifact's attribution header points at.

- Upstream: `anthropics/html-effectiveness`, MIT, `Copyright (c) 2026 Anthropic PBC`
- **Filename MUST NOT be `LICENSE`.** The payload builder special-cases the
  exact relative path `LICENSE` and maps it to this repository's own root
  license. The chosen name is `UPSTREAM-NOTICE.md`.

## Entity 8 — Gallery Artifact (contract only in ART-001)

ART-001 ships **zero** artifacts. The entity is defined here because the
validation and the contract that ART-002…005 inherit are ART-001's deliverable:
a single self-contained file that embeds both marked blocks verbatim, renders
from `file://`, loads nothing external except the two font hosts, and — when
`source.origin` is `upstream` — carries the FR-020 attribution header.
