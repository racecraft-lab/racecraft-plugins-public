# Implementation Plan: Brand identity and marketplace landing page

**Branch**: `doc-013-brand-identity-marketplace-landing` | **Date**: 2026-06-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/doc-013-brand-identity-marketplace-landing/spec.md`

## Summary

Apply the Racecraft visual identity to the speckit-pro docs site (Astro 6.4.6 +
Starlight 0.40.0 at `docs-site/`) and convert the stock-Starlight home route into a
real marketplace landing page. The technical approach: a single `brand.css` maps the
Racecraft palette onto Starlight's `--sl-color-*` custom properties (blue accent for
links/active-nav, AA-safe `#2a6a99` for link text, red `#dc143c` reserved as
punctuation, soft dark-gray `#1a1a1a` reading surface with true-black scoped to the
hero only), declares five self-hosted woff2 `@font-face`s with `font-display: swap`,
and points Starlight's font tokens at Space Grotesk / Geist / Fira Code. Brand assets
(5 fonts, 10 favicon/manifest files, 3 logo SVGs) are ported verbatim from the
sibling `landing-page/website` project. `astro.config.mjs` wires `customCss`, `logo`
(light/dark wordmark, `replacesTitle`), `favicon`, and font-preload `head` tags. The
home route `index.mdx` becomes a Starlight-native `template: splash` + `hero` +
`<CardGrid>` landing with the logomark hero image, a primary CTA to
`/racecraft-plugins-public/first-run/`, and a secondary CTA to the GitHub repo. One
thin vertical slice — no split.

## Technical Context

**Language/Version**: Docs-site JavaScript ESM on Node >=22.12 (nvm `v22.22.2`);
CSS; Markdown/MDX content. No application source language.

**Primary Dependencies**: Astro 6.4.6, Starlight 0.40.0, `starlight-links-validator`
0.24.1 (existing); pnpm 10.25.0 via `pnpm --dir docs-site …`. No new runtime
dependency — fonts copied verbatim (no subsetting toolchain added).

**Storage**: Checked-in repository files only (CSS, MDX, SVG, woff2, favicon PNG/ICO,
`site.webmanifest`). No database, no browser storage, no runtime state.

**Testing**: `pnpm --dir docs-site validate` (Astro check + `starlight-links-validator`
build + safe-aids + docs-quality + Playwright smoke-preview). Repo deterministic suite
`bash tests/speckit-pro/run-all.sh` is unaffected (no plugin/test-suite files touched).

**Target Platform**: Static GitHub Pages site under `base: '/racecraft-plugins-public'`,
`trailingSlash: 'always'`; modern browsers, light + dark mode.

**Project Type**: Static documentation site (Astro/Starlight). Brand-styling + content
slice — not a library/CLI/service.

**Performance Goals**: N/A for this slice — a performance/Lighthouse budget is **DOC-017**.
DOC-013 keeps payload lean (5-woff2 set, 2 preloads) to leave headroom but does not own
a perf target.

**Constraints**: Both light and dark mode MUST meet WCAG AA (FR-014). Text visible
during font load via system fallback (FR-008). Reduced-motion respected (FR-015).
`pnpm --dir docs-site validate` MUST pass. Stay within `docs-site/` brand surfaces;
no per-component restyle (DOC-016), no perf budget (DOC-017), no verbal-voice system
(DOC-019), no domain/base-path cutover (DOC-012).

**Scale/Scope**: One home/landing route rewritten; site-wide token + font + logo +
favicon application via one stylesheet and config edits. 2 user stories, 17 FRs, 8 SCs.

**Reviewability Budget**: Primary surface = **UI** (docs-site brand styling + landing
route). Secondary = seed/config (Starlight config for logo/favicon/customCss/font
preload) + binary assets (woff2, SVG, favicon set) declared **non-reviewable**.
Projected reviewable LOC ≈ **80 CSS** + a small MDX landing file + a handful of config
lines (binary assets excluded); design-concept estimator reported ~395 LOC total
across the slice. Projected production files: **1–2** (brand stylesheet + landing
content). Projected total text/config files: **6–8** plus binary assets. **Budget
result: within budget. Split decision: single vertical slice — no split.**

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block. Binary assets (woff2/SVG/PNG/ICO/webmanifest) are declared but are
non-reviewable artifacts under the budget and are not counted toward reviewable LOC.

- NEW docs-site/src/styles/brand.css
- MODIFIED docs-site/astro.config.mjs
- MODIFIED docs-site/src/content/docs/index.mdx
- NEW docs-site/src/assets/logo.svg
- NEW docs-site/src/assets/logo-light.svg
- NEW docs-site/src/assets/mark.svg
- NEW docs-site/public/site.webmanifest
- NEW docs-site/public/favicon.svg
- NEW docs-site/public/favicon.ico
- NEW docs-site/public/favicon-16x16.png
- NEW docs-site/public/favicon-32x32.png
- NEW docs-site/public/favicon-32x32-light.png
- NEW docs-site/public/favicon-48x48.png
- NEW docs-site/public/apple-touch-icon.png
- NEW docs-site/public/android-chrome-192x192.png
- NEW docs-site/public/android-chrome-512x512.png
- NEW docs-site/public/fonts/space-grotesk-400.woff2
- NEW docs-site/public/fonts/space-grotesk-700.woff2
- NEW docs-site/public/fonts/geist-400.woff2
- NEW docs-site/public/fonts/geist-600.woff2
- NEW docs-site/public/fonts/fira-code-regular.woff2

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Constitution v1.1.0. The relevant principles for a docs-site brand slice (no plugin
code, no bash scripts):

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Plugin Structure Compliance | **N/A — pass** | No plugin manifest/command/agent/skill/hook touched; this is `docs-site/` only. Layer-1 plugin-payload guard is unaffected (no files added under `speckit-pro/`). |
| II. Script Safety | **N/A — pass** | No bash scripts created or modified. |
| III. Semantic Versioning | **N/A — pass** | No `plugin.json` version edit; release-please untouched. |
| IV. Test Coverage Before Merge | **pass** | No new bash scripts (no Layer-4 owed). Verification = `pnpm --dir docs-site validate` (the docs-site gate, run by CI `validate-docs`); `bash tests/speckit-pro/run-all.sh` stays green (no plugin/test files changed). |
| V. Conventional Commits | **pass** | PR/commits use `feat(docs-site): …` or `docs: …`, plain-English public-readable title. |
| VI. KISS, Simplicity & YAGNI | **pass** | Starlight-native splash/hero/CardGrid + token mapping — no bespoke components, no font-subsetting toolchain, no speculative flags. Fonts/favicons/logos copied verbatim. Simplest faithful path. |

**Reviewability gate (constitution + plan-template thresholds)**: warn above 400
reviewable LOC / 6 production files / 15 total files / >1 primary surface; block above
800 / 8 / 25 / >1 primary surface. This slice: ~80 reviewable CSS LOC + small MDX +
config lines (well under 400); **2 production files** (`brand.css`, `index.mdx`) under
6; **6–8 text/config files** under 15; **one primary surface (UI)**. Binary font/
favicon/logo assets are declared non-reviewable. **Within budget — no block, no warn
on size.** (The reviewability *setup* gate warns only on the primary-surface count
heuristic, not size; primary surface is a single UI surface here.)

**Split decision**: Remains a single vertical slice — brand tokens + fonts + logo +
favicon + landing hero delivered end-to-end. Estimator `suggested_slices: 1`,
`status: ok`. **No split.** Deferred work is owned by named follow-up specs (not a
split of this slice): per-component restyle **DOC-016**, perf/Lighthouse budget
**DOC-017**, verbal-voice/tone system **DOC-019**, custom domain / base-path cutover
**DOC-012**.

**PR review packet source** (per spec's PR Review Packet Requirements):
- **What changed**: `brand.css` (token map + fonts), `astro.config.mjs` (logo/favicon/
  customCss/preload), `index.mdx` (splash landing), + ported binary assets.
- **Why**: brand the marketplace docs + give newcomers a real landing entry point.
- **Non-goals**: DOC-016 / DOC-017 / DOC-019 / DOC-012 (named above).
- **Review order**: (1) `brand.css` token map + `@font-face`; (2) `astro.config.mjs`
  wiring; (3) `index.mdx` landing content; (4) spot-check ported assets exist.
- **Scope budget**: as in Reviewability Budget above.
- **Traceability**: FR-005/005a/006 → `brand.css` token map + recorded contrast ratios
  (red-as-punctuation guard: white-on-red CTA fill, no failing red text); FR-007/008 →
  `@font-face` set + preload tags; FR-009/010/011 → `astro.config.mjs` `logo`/`favicon`
  + ported assets + `index.mdx` `hero.image` (with `alt` per FR-010); FR-001–004 →
  `index.mdx` splash content; FR-013 → scoped hero-block rule + soft-dark `#1a1a1a`
  surface in `brand.css`; FR-014a → visible focus-ring rule (`#3c89c6`, ≥3:1 both
  modes) in `brand.css`.
- **Verification**: `pnpm --dir docs-site validate` passing + a recorded WCAG AA
  contrast check for brand-accent text in BOTH modes.
- **Known gaps**: hero copy authored at Implement; dark-hero logomark legibility
  verified visually; lab texture omitted unless plain.
- **Rollback/flags**: revert is a clean delete of `brand.css` + ported assets and a
  restore of `astro.config.mjs` / `index.mdx` (no migration, no flag, no data).

**Result: Constitution Check PASSES. No violations — Complexity Tracking not required.**

## Project Structure

### Documentation (this feature)

```text
specs/doc-013-brand-identity-marketplace-landing/
├── spec.md              # Feature spec (input)
├── brand-guide.md       # Brand port-and-map reference (input)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — investigation findings + token map
├── data-model.md        # Phase 1 output — brand entities
├── quickstart.md        # Phase 1 output — validation guide
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

(No `contracts/` directory — this feature exposes no API/CLI/schema interface. The
"contract" surface is the rendered UI + the Starlight config, validated by
`pnpm --dir docs-site validate`; see quickstart.md scenarios.)

### Source Code (repository root)

```text
docs-site/
├── astro.config.mjs                 # MODIFIED: + customCss, logo, favicon; append head preload/favicon/theme tags
├── public/
│   ├── robots.txt                   # untouched (existing)
│   ├── favicon.svg                  # NEW (ported)
│   ├── favicon.ico                  # NEW (ported)
│   ├── favicon-16x16.png            # NEW (ported)
│   ├── favicon-32x32.png            # NEW (ported)
│   ├── favicon-32x32-light.png      # NEW (ported)
│   ├── favicon-48x48.png            # NEW (ported)
│   ├── apple-touch-icon.png         # NEW (ported)
│   ├── android-chrome-192x192.png   # NEW (ported)
│   ├── android-chrome-512x512.png   # NEW (ported)
│   ├── site.webmanifest             # NEW (ported; theme_color #dc143c, background_color #f1f0ec)
│   └── fonts/
│       ├── space-grotesk-400.woff2  # NEW (ported)
│       ├── space-grotesk-700.woff2  # NEW (ported, preloaded)
│       ├── geist-400.woff2          # NEW (ported, preloaded)
│       ├── geist-600.woff2          # NEW (ported)
│       └── fira-code-regular.woff2  # NEW (ported)
└── src/
    ├── assets/
    │   ├── logo.svg                 # NEW (ported — dark wordmark)
    │   ├── logo-light.svg           # NEW (ported — light wordmark)
    │   └── mark.svg                 # NEW (ported — logomark / hero image)
    ├── styles/
    │   └── brand.css                # NEW: --sl-color-* token map (light+dark) + 5 @font-face + font tokens + scoped red/hero-block + reduced-motion
    └── content/docs/
        └── index.mdx                # MODIFIED: rewrite to template: splash + hero + CardGrid
```

**Structure Decision**: All changes live under the existing `docs-site/` Astro/
Starlight tree. Two production text files (`src/styles/brand.css`, `src/content/docs/
index.mdx`) carry the reviewable LOC; one config file (`astro.config.mjs`) is edited;
the remaining 18 entries are ported binary brand assets (non-reviewable). No new
top-level directory; `src/styles/` is the only new subdirectory.

## File-by-file change list

1. **`docs-site/src/styles/brand.css`** *(NEW, primary reviewable surface, ~80 LOC)*:
   `:root` (dark default) + `:root[data-theme='light']` blocks setting the
   `--sl-color-*` token map from research.md Decision 5; five `@font-face` blocks
   (`font-display: swap`) for the ported woff2; font-token assignments
   (`--sl-font` → Geist, `--sl-font-mono` → Fira Code, heading selectors → Space
   Grotesk); a scoped rule applying brand red `#dc143c` to the splash hero CTA **as
   white-text-on-red fill** (`#ffffff` on `#dc143c` = 4.99:1, AA-pass per FR-005a —
   red is NOT applied as normal-size red text on the warm base `#f1f0ec` 4.38:1 or the
   hero block `#0a0a0a` 3.97:1, both of which fail AA normal-text) and a true-black
   `#0a0a0a` hero block only; a visible keyboard focus-ring using the non-text blue
   `#3c89c6` meeting ≥3:1 in both modes (3.30:1 on `#f1f0ec`, 4.63:1 on `#1a1a1a`) per
   FR-014a; dark-mode body text set to near-white `#e6e6e6` (not pure white) per
   FR-014; and a `@media (prefers-reduced-motion: reduce)` guard suppressing entrance
   animation.
2. **`docs-site/astro.config.mjs`** *(MODIFIED)*: inside the existing `starlight({…})`
   call add `customCss: ['./src/styles/brand.css']`, `logo: { light:
   './src/assets/logo.svg', dark: './src/assets/logo-light.svg', replacesTitle: true,
   alt: 'Racecraft' }`, `favicon: '/favicon.svg'`; **append** to the existing `head`
   array the two font `<link rel="preload">` tags ONLY (Space Grotesk 700 + Geist 400 —
   base-path-prefixed, **each carrying the `crossorigin` attribute** per FR-008; the
   other 3 faces MUST NOT be preloaded) plus any favicon/`apple-touch-icon`/manifest
   `<link>` and `theme-color` `<meta>` tags. Leave the existing robots `<meta>` and `sidebar` intact.
3. **`docs-site/src/content/docs/index.mdx`** *(MODIFIED, rewrite)*: frontmatter
   `template: splash` + `hero` (benefit-led `title` per FR-002, plain-English
   `tagline` value-prop, `image: { light/dark: mark.svg }`, `actions`: **exactly one
   primary** → `/racecraft-plugins-public/first-run/` with `variant: 'primary'`, and
   **one subordinate secondary** → GitHub repo with `variant: 'secondary'` or
   `'minimal'` — no third/competing action, per FR-003a); body imports
   `CardGrid`/`Card` from `@astrojs/starlight/components` and renders the value-prop
   cards (3 by default, 2–4 range per FR-004), each a scannable benefit-led title +
   plain-English blurb. The above-the-fold set {mark, headline, value-prop, primary
   CTA} must fit the first screen on desktop and mobile (FR-001a). Copy authored at
   Implement against the brand-guide §6 anti-hype tone made testable in FR-004a
   (no hype/superlatives, no unexplained jargon); direction locked.
4. **`docs-site/src/assets/{logo.svg, logo-light.svg, mark.svg}`** *(NEW, ported
   verbatim)*: wordmark + logomark SVGs (Starlight imports `logo` from `src/`).
5. **`docs-site/public/{favicon set + site.webmanifest}`** *(NEW, ported verbatim,
   10 files)*: favicon SVG/ICO/PNGs + `apple-touch-icon` + android-chrome 192/512 +
   `site.webmanifest`. Placed alongside (not disturbing) `robots.txt`.
6. **`docs-site/public/fonts/{5 woff2}`** *(NEW, ported verbatim)*: the lean weight
   set (Space Grotesk 400/700, Geist 400/600, Fira Code regular).

## Phasing (Implement-phase sequencing — for tasks.md)

- **Phase A — Port binary assets** (no reviewable LOC): copy the 5 woff2 → `public/
  fonts/`, the 10 favicon/manifest files → `public/`, the 3 logo SVGs → `src/assets/`.
  Verify each lands and `robots.txt` is untouched.
- **Phase B — Brand stylesheet**: author `src/styles/brand.css` (token map + @font-face
  + font tokens + scoped red/hero-block + reduced-motion). This is the bulk of the
  reviewable LOC.
- **Phase C — Wire config**: edit `astro.config.mjs` (customCss, logo, favicon, append
  head preload/favicon/theme tags).
- **Phase D — Landing route**: rewrite `index.mdx` to splash + hero + CardGrid; author
  hero copy + ~3 cards; set primary CTA → `/racecraft-plugins-public/first-run/`,
  secondary → GitHub.
- **Phase E — Validate**: run `pnpm --dir docs-site validate`; walk quickstart.md
  scenarios 1–16 in both light and dark mode; **record the WCAG AA contrast ratios as
  an enumerated table** covering link text, body text, the non-text blue accent, the
  keyboard focus ring, and red punctuation in both modes as PR evidence (each pair with
  its measured ratio + threshold; confirm red appears only in a passing pattern and the
  focus ring meets ≥3:1). Spot-check that the hero `hero.image` carries an `alt` value.
  Confirm no scope leaked into DOC-016/017/019/012.

Dependencies: B depends on A (the `@font-face` `src` paths reference the ported
files); C depends on A+B (config references `brand.css` + the logo/favicon assets);
D depends on A (hero references `mark.svg`); E depends on A–D.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
