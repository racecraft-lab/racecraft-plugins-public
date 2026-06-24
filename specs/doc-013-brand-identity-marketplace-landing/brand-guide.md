# Racecraft Brand Guide

> **Source of truth:** the sibling `landing-page/website` project
> (`src/styles/global.css`, `public/site.webmanifest`, and
> `src/assets/images/logos/`). This guide is a port-and-map reference for
> DOC-013, which applies the same identity to the speckit-pro docs site
> (Astro + Starlight at `docs-site/`). When a value here disagrees with the
> live landing-page CSS, the landing-page CSS wins — re-audit before porting.

## 1. Color

### Primary brand colors

| Token | Hex | Use |
| ----- | --- | --- |
| Brand Red | `#dc143c` | Primary accent, logo mark, `theme_color`, destructive |
| Brand Blue | `#3c89c6` | CTAs, primary, links, focus ring |
| Brand Blue (dark) | `#2a6a99` | Blue on white text — WCAG AA (5.0:1 vs 3.75:1) |
| Brand Orange | `#e74900` | Tertiary accent / highlight |

### Warm neutral base (Pantone 2025/2026 "Mocha Mousse" alignment, 70-20-10)

| Token | Hex | Role |
| ----- | --- | ---- |
| pantone-base | `#f1f0ec` | Primary page background (light) |
| pantone-lighter | `#f7f6f4` | Sidebar / raised surface |
| pantone-light | `#f4f3f0` | Secondary / accent surface |
| pantone-medium | `#eeecea` | — |
| pantone-dark | `#e8e7e3` | Borders (subtle definition on warm base) |
| pantone-deeper | `#e0ded9` | — |

### Neutral scale (text, borders, UI)

`#ffffff` · 400 `#9ca3af` · 500 `#6b7280` · 600 `#4b5563` · 700 `#374151` · 800 `#1f2937` · 900 `#111827`

### Light mode (Racecraft.co corporate)

```
background #f1f0ec · foreground #111827 · card #ffffff
primary #3c89c6 (fg #ffffff) · secondary #f4f3f0 (fg #3c89c6)
muted #f7f7f7 (fg #6b7280) · accent #f4f3f0 (fg #3c89c6)
destructive #dc143c (fg #ffffff) · border #e8e7e3 · ring #3c89c6 · sidebar #f7f6f4
```

### Dark mode (GTO90 creative)

```
background #0a0a0a · foreground #ffffff · card #1f2937
primary #3c89c6 (fg #ffffff) · secondary #374151
destructive #dc143c · border rgba(255,255,255,0.1) · sidebar #1f2937
```

GTO90 section variants (dark): hero `#0a1628` · content `#1e1e1e` ·
accent-red `#450a15` · accent-orange `#5c1d00` · footer `#111827`.

### Webmanifest

`theme_color: #dc143c` · `background_color: #f1f0ec`

## 2. Typography

Self-hosted woff2, `font-display: swap`, no external DNS. Port the files from
`landing-page/website/public/fonts/`.

| Role | Family | Weights (woff2) | Use |
| ---- | ------ | --------------- | --- |
| Display | **Space Grotesk** | 300/400/500/600/700 | H1, H2, buttons, nav |
| Body | **Geist** | 400/500/600/700/800 | H3–H6, body, UI |
| Mono | **Fira Code** | 400/500/600 | code blocks, inline code |

Type scale: display `3.5rem` · h1 `2.5rem` · h2 `2rem` · h3 `1.5rem` ·
body-lg `1.125rem` · body `1rem` · small `0.875rem`.

Stacks: `"Space Grotesk", system-ui, sans-serif` · `"Geist", system-ui,
sans-serif` · `"Fira Code", monospace`.

## 3. Logos & mark

Port from `landing-page/website/src/assets/images/logos/`.

| Asset | File | Viewbox | Colors |
| ----- | ---- | ------- | ------ |
| Wordmark (dark) | `logo.svg` | `0 0 1956 287` | text `#111827`, mark `#dc143c` |
| Wordmark (light) | `logo-light.svg` | `0 0 1956 287` | text `#ffffff`, mark `#dc143c` |
| Logomark / icon | `mark.svg` | `0 0 1250 1041` | shape `#111827`, accent `#dc143c` |

Use the light wordmark on dark backgrounds (dark mode, GTO90 sections); the
dark wordmark on the warm light base. The mark drives the favicon set.

## 4. Favicon / webmanifest assets

Port the full set from `landing-page/website/public/`:
`favicon.svg`, `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`,
`favicon-32x32-light.png`, `favicon-48x48.png`, `apple-touch-icon.png`,
`android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest`.

## 5. Radius, motion, texture

Radius: sm `0.225rem` · md `0.425rem` · base `0.775rem` · lg `0.625rem` ·
xl `1.025rem` · 2xl `1rem`.

Motion: fast `150ms` · normal `300ms` · slow `500ms`; ease-out
`cubic-bezier(0.4, 0, 0.2, 1)`. All entrance animations must respect
`prefers-reduced-motion: reduce`.

Lab texture: subtle grid + dot overlay (`rgba(0,0,0,0.05)` grid,
`rgba(0,0,0,0.03)` dots) for a technical/lab feel — optional for docs.

## 6. Verbal tone (reference only)

DOC-013 is **visual** identity. Captured here only to keep copy on-brand;
a dedicated verbal-voice system is DOC-019.

Hero on landing-page reads: headline *"Can AI agents really build production
games?"*; sub *"We're cutting through the hype by building GTO90™ in public.
Real engineering decisions, unfiltered outcomes, zero AI evangelism."*; CTA
*"Read Articles"*.

Essence: **pragmatic, transparent, anti-hype.** Skeptical authority,
no marketing fluff, technical credibility, public-first. For the docs
marketplace landing, the analog is a confident, plain-English value prop for
spec-driven development — not breathless feature-listing.

## 7. DOC-013 mapping notes (Starlight)

- Map brand colors to Starlight `--sl-color-*` tokens (accent → blue family;
  keep red for the mark/hero accent) for both light and dark.
- Wire `brand.css` via `customCss` in `astro.config.mjs`; set `logo` +
  `favicon`.
- Self-host fonts with `<link rel="preload">` for the display + body woff2.
- Landing route (`docs-site/src/content/docs/index.mdx`) becomes a branded
  hero + value-prop block, not a generic doc page.
- Out of scope (per roadmap): per-component a11y restyle (DOC-016),
  performance budget (DOC-017).
