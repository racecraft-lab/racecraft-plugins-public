# Data Model: Brand identity and marketplace landing page (DOC-013)

**Date**: 2026-06-23 | **Branch**: `doc-013-brand-identity-marketplace-landing`

This feature has no runtime database. The "entities" are the brand-design data
structures from the spec's **Key Entities** section: the token set, the typeface
set, the logo asset set, and the landing content model. Each is a static,
checked-in configuration/asset — they are modeled here as the authoritative
field definitions the Implement phase fills in. Validation rules trace to the
functional requirements and success criteria.

---

## Entity 1 — Brand color token set

The named brand colors and their mapping to Starlight `--sl-color-*` roles, per
light and dark mode. Defined in `docs-site/src/styles/brand.css`.

**Fields** (role → value, by mode):

| Role (Starlight token) | Light value | Dark value | Source token |
| ---------------------- | ----------- | ---------- | ------------ |
| `--sl-color-accent` (non-text accent) | `#3c89c6` | `#3c89c6` | Brand Blue |
| `--sl-color-accent-low` | `#d6e4f0` | `#13283a` | blue tint |
| `--sl-color-accent-high` / `--sl-color-text-accent` (link text) | `#2a6a99` | `#7cb3dd` | AA-safe blue (light) / lightened blue (dark) |
| `--sl-color-text` (body fg) | `#111827` | `#e6e6e6` | neutral-900 / near-white |
| `--sl-color-white` (strongest fg) | `#111827` | `#ffffff` | — |
| `--sl-color-bg` (reading surface) | `#f1f0ec` | `#1a1a1a` | pantone-base / soft-dark |
| `--sl-color-bg-sidebar` / `-nav` | `#f7f6f4` | `#1f2937` | pantone-lighter / brand dark card |
| border / hairline | `#e8e7e3` | `rgba(255,255,255,0.10)` | pantone-dark / brand dark border |
| Hero block background (scoped) | n/a | `#0a0a0a` | GTO90 true-black (hero only) |
| `theme_color` (webmanifest, not a CSS token) | `#dc143c` | `#dc143c` | Brand Red |

**Validation rules**:
- VR-1 (FR-005): `#dc143c` (red) MUST appear only as logo-mark fill, webmanifest
  `theme_color`, and the scoped hero/CTA treatment — never as `--sl-color-accent`
  or any link/active-nav color.
- VR-2 (FR-006 / SC-003): link-sized text color MUST be `#2a6a99` (light) /
  `#7cb3dd` (dark) and meet WCAG AA against its background in both modes.
- VR-3 (FR-013 / SC-004): `--sl-color-bg` (reading surface) in dark mode MUST be a
  soft dark-gray in `#121212`–`#1e1e1e` (chosen `#1a1a1a`); true black `#0a0a0a`
  MUST be scoped to the hero block only.
- VR-4 (FR-012 / SC-002): every token MUST be defined for BOTH modes; no role may
  fall back to stock-Starlight default.

**State**: two states — `[data-theme='light']` and `:root` (dark, default). Theme
toggle switches the active token set; correct light/dark logo + accent variants
apply with no flash of the wrong theme (FR/AS Story-2 #3).

---

## Entity 2 — Brand typeface set

The display, body, and monospace typefaces, the shipped weights, and their role
assignment. `@font-face` blocks + font-token assignments live in `brand.css`;
woff2 binaries live in `docs-site/public/fonts/`.

**Fields** (one row per shipped face — the lean set, FR-007):

| Family | Weight | Role | woff2 file (ported verbatim) | Preloaded? |
| ------ | ------ | ---- | ---------------------------- | ---------- |
| Space Grotesk | 400 | Display regular (H1/H2/nav/buttons) | `space-grotesk-400.woff2` | no |
| Space Grotesk | 700 | Display bold (above-the-fold) | `space-grotesk-700.woff2` | **yes** |
| Geist | 400 | Body / UI regular | `geist-400.woff2` | **yes** |
| Geist | 600 | Body semibold (H3–H6 weight) | `geist-600.woff2` | no |
| Fira Code | 400 | Code (blocks + inline) | `fira-code-regular.woff2` | no |

**Font-token assignment** (in `brand.css`):
- `--sl-font` → `"Geist", system-ui, sans-serif`
- `--sl-font-mono` → `"Fira Code", ui-monospace, monospace`
- Heading/display selectors → `"Space Grotesk", system-ui, sans-serif`

**Validation rules**:
- VR-5 (FR-007): exactly these 5 faces ship — display regular+bold, body
  regular+semibold, mono regular. No other weights are added to `public/fonts/`.
- VR-6 (FR-008 / SC-005): every `@font-face` MUST set `font-display: swap`; each
  stack MUST begin with a system fallback so text is visible during load; fonts
  MUST be served locally (no external font-host request / no external DNS).
- VR-7 (FR-008): `space-grotesk-700.woff2` and `geist-400.woff2` MUST be
  `<link rel="preload" as="font" type="font/woff2" crossorigin>` in the config
  `head` (base-path-prefixed href).
- VR-8 (naming): the Fira Code face references the `fira-code-regular.woff2`
  filename (source uses `-regular`, not `-400`).

---

## Entity 3 — Brand logo assets

The light/dark wordmark variants (header), the logomark (hero image), and the
favicon/browser-icon set. Wordmarks live under `docs-site/src/assets/`; favicons
under `docs-site/public/`.

**Fields**:

| Asset | File | Location | viewBox | Colors (verified) | Role |
| ----- | ---- | -------- | ------- | ----------------- | ---- |
| Wordmark (dark) | `logo.svg` | `src/assets/` | `0 0 1956 287` | text `#111827`, mark `#dc143c` | header `logo.light` (on warm light surface) |
| Wordmark (light) | `logo-light.svg` | `src/assets/` | `0 0 1956 287` | text `#ffffff`, mark `#dc143c` | header `logo.dark` (on dark surface) |
| Logomark | `mark.svg` | `src/assets/` | `0 0 1250 1041` | shape `#111827`, accent `#dc143c` | splash `hero.image` (light + dark) |
| Favicon set | `favicon.svg`, `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon-32x32-light.png`, `favicon-48x48.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png` | `public/` | — | mark-derived | browser tab / platform UI |
| Webmanifest | `site.webmanifest` | `public/` | — | `theme_color #dc143c`, `background_color #f1f0ec` | PWA/platform metadata |

**Header logo config** (`astro.config.mjs`):
```
logo: { light: './src/assets/logo.svg', dark: './src/assets/logo-light.svg',
        replacesTitle: true, alt: 'Racecraft' }
```

**Validation rules**:
- VR-9 (FR-009): header MUST show the wordmark (not plain text); `replacesTitle:
  true` keeps the `title` string as the accessible site name; the header logo MUST
  remain the home link.
- VR-10 (FR-009 / FR-010 / AS Story-2 #3): the dark wordmark variant shows in light
  mode and the light wordmark variant in dark mode (mark never disappears against a
  same-color background); same light/dark behavior for the hero logomark.
- VR-11 (FR-010): the splash hero image MUST be the `mark.svg` logomark, correct
  variant per mode (single source asset reused for both; dark-surface legibility
  verified at Implement).
- VR-12 (FR-011): the full favicon set + `theme_color #dc143c` MUST be wired so the
  brand mark appears in the browser tab and platform UI.
- VR-13: porting MUST NOT disturb the existing `public/robots.txt`.

---

## Entity 4 — Landing page content

The hero headline, tagline/value-prop body, CTA targets, and the ~3 value-prop
card titles/blurbs. Authored in `docs-site/src/content/docs/index.mdx` using
`template: splash` + `hero` frontmatter + `<CardGrid>`/`<Card>`.

**Fields**:

| Field | Constraint / value | Source |
| ----- | ------------------ | ------ |
| `template` | `splash` (full-width hero, not article layout) | FR-001 |
| `hero.title` | benefit-led headline (plain-English, anti-hype) — wording authored at Implement | FR-002, brand §6 |
| `hero.tagline` | short value-prop body for spec-driven development | FR-002 |
| `hero.image` | `{ light: mark.svg, dark: mark.svg }` (logomark) | FR-010 |
| `hero.actions[0]` (primary CTA) | text + link → **`/racecraft-plugins-public/first-run/`** (getting-started/first-workflow tutorial), `variant: primary` | FR-003, SC-006 |
| `hero.actions[1]` (secondary CTA) | text → `https://github.com/racecraft-lab/racecraft-plugins-public`, `variant: minimal/secondary` | FR-003, SC-006 |
| Value-prop cards | ~3 `<Card>` in a `<CardGrid>`; plain, anti-hype titles + blurbs — wording authored at Implement | FR-004, AS Story-1 #3 |

**Validation rules**:
- VR-14 (FR-001 / AS Story-1 #1): the home route MUST render as a splash landing
  (mark + headline + value-prop + primary CTA + secondary CTA), NOT a generic
  doc article with a sidebar body.
- VR-15 (FR-003 / SC-006): primary CTA MUST resolve to
  `/racecraft-plugins-public/first-run/` and secondary to the GitHub repo, with no
  broken links (`starlight-links-validator` enforces this on build).
- VR-16 (FR-004): approximately three value-prop cards, plain anti-hype language.
- VR-17 (FR-002 / SC-001): the mark, headline, value-prop, and a distinguished
  primary CTA MUST be comprehensible within the first screen (no scroll).
- VR-18 (FR-001 / Assumptions): built from Starlight-native splash/hero/CardGrid —
  no bespoke custom page components.
- VR-19 (Edge case / FR-015 / SC-008): any entrance animation MUST respect
  `prefers-reduced-motion: reduce`.

---

## Cross-entity invariants

- **INV-1 (FR-012 / SC-002)**: the brand identity (all four entities) applies across
  BOTH modes and ALL routes, not only the landing page — tokens/fonts/logo/favicon
  are global (config + `brand.css`), landing content is the one route-specific piece.
- **INV-2 (FR-016)**: every value traces to `brand-guide.md`; where the guide was
  ambiguous, the live `landing-page/website` source was re-checked and wins
  (resolved in `research.md` — no remaining ambiguities).
- **INV-3 (FR-017 / SC-007)**: the model introduces no per-component restyle
  (DOC-016), no perf budget (DOC-017), no verbal-voice system (DOC-019), and no
  domain/base-path cutover (DOC-012).
