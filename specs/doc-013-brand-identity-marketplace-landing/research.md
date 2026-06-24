# Research: Brand identity and marketplace landing page (DOC-013)

**Date**: 2026-06-23 | **Branch**: `doc-013-brand-identity-marketplace-landing`

This document records the file-evidence investigation that resolves the three
open questions deferred from the design concept, plus the concrete brand → Starlight
token map. All findings come from inspecting (not modifying) the sibling brand-source
project (the `landing-page` checkout, a peer directory alongside this repository)
and the current `docs-site/` config. Where the brand guide disagreed with the live
source, the live source wins (FR-016).

---

## Decision 1 — Font sourcing: COPY the existing woff2 verbatim (no re-subset)

**Decision**: Port the existing `.woff2` files from
`landing-page/website/public/fonts/` byte-for-byte into `docs-site/public/fonts/`.
Do **not** re-subset to Latin in this slice.

**Rationale**:
- The source files are already small, subset woff2: Space Grotesk weights are
  ~12.8–13.4 KB each, Fira Code ~23 KB each, Geist ~45–46 KB each. These sizes
  indicate the source already shipped a subset (full unhinted woff2 for these
  families would be larger). Re-subsetting would add a build dependency
  (`fonttools`/`glyphhanger`) for a marginal byte saving — a direct YAGNI/KISS
  violation against the constitution and the design-concept's "keep payload lean"
  note. DOC-017 owns any future perf budget; DOC-013 ships the lean weight set
  and stops there.
- Copying verbatim is the lowest-LOC, lowest-risk path and keeps the fonts
  identical to the production Racecraft site (brand fidelity).

**Alternatives considered**: Re-subset to Latin via a build step (rejected: new
tooling dependency, negligible gain, out of scope for this slice); pull from an
external font host (rejected: FR-008 mandates local self-hosting, no external DNS).

**Exact woff2 filenames to PORT (5 files, lean set per FR-007 / design Q4)**:

| Source file (verbatim) | Family | Weight | Role |
| ---------------------- | ------ | ------ | ---- |
| `space-grotesk-400.woff2` | Space Grotesk | 400 | Display regular |
| `space-grotesk-700.woff2` | Space Grotesk | 700 | Display bold (preload) |
| `geist-400.woff2` | Geist | 400 | Body regular (preload) |
| `geist-600.woff2` | Geist | 600 | Body semibold |
| `fira-code-regular.woff2` | Fira Code | 400 | Monospace / code |

**Confirmation of required weights** (all present in source):
- Space Grotesk: source ships 300/400/500/600/700 → **400 ✅ and 700 ✅** available.
- Geist: source ships 400/500/600/700/800 → **400 ✅ and 600 ✅** available.
- Fira Code: source ships `regular`(400)/`medium`(500)/`semibold`(600) →
  **400 ✅** available (file named `fira-code-regular.woff2`, not `fira-code-400.woff2`
  — note the naming difference; the `@font-face` block must reference the
  `-regular` filename).

**Files NOT ported** (available in source but excluded to keep the set lean):
`space-grotesk-300/500/600`, `geist-500/700/800`, `fira-code-medium/semibold`.

**Preload decision** (FR-008): preload only `space-grotesk-700.woff2` (display bold,
above-the-fold hero/H1) and `geist-400.woff2` (body regular). All five faces use
`font-display: swap`.

---

## Decision 2 — Favicons + webmanifest: PORT the full set verbatim

**Decision**: Copy the full favicon/icon set and `site.webmanifest` from
`landing-page/website/public/` into `docs-site/public/`, alongside the existing
`robots.txt` (which is left untouched).

**Exact files present in source `public/` and to be ported (10 files)**:

| File | Notes |
| ---- | ----- |
| `favicon.svg` | SVG favicon (shares the `mark.svg` geometry; fills `#261c02` + `#e71939`) |
| `favicon.ico` | 15 KB multi-res ICO |
| `favicon-16x16.png` | |
| `favicon-32x32.png` | |
| `favicon-32x32-light.png` | light-variant 32px (for dark UA chrome) |
| `favicon-48x48.png` | |
| `apple-touch-icon.png` | |
| `android-chrome-192x192.png` | referenced by webmanifest |
| `android-chrome-512x512.png` | referenced by webmanifest |
| `site.webmanifest` | see colors below |

**`site.webmanifest` contents (verbatim from source)** — theme/background colors:
- `name`: `"Racecraft Technical Innovation Lab"`
- `short_name`: `"Racecraft"`
- `theme_color`: **`#dc143c`** (brand red — FR-011, matches brand guide §4)
- `background_color`: **`#f1f0ec`** (pantone-base warm neutral)
- `display`: `"standalone"`
- `icons`: android-chrome 192 + 512 (paths `/android-chrome-…` — see base-path note)

**Base-path note (carry into Implement, NOT a blocker)**: the source manifest icon
`src` values are root-absolute (`/android-chrome-192x192.png`). The docs-site is
served under `base: '/racecraft-plugins-public'`. Whether to leave these root-absolute
or prefix the base path is an Implement-phase detail; FR-011 only requires the
favicon set + theme color to apply. Files in `docs-site/public/` are copied to the
site root and the `<link rel="icon">`/manifest `<link>` tags are emitted by the
Starlight `head` config, so the head-tag hrefs must include the base prefix.

**Rationale**: FR-011 requires the brand favicon set + theme color; the source set
already exists (Assumptions). Porting verbatim is the simplest faithful path.

**Alternatives considered**: regenerate from `mark.svg` (rejected: source set already
exists, regeneration adds tooling for no benefit).

---

## Decision 3 — Logos: all three assets confirmed present; fills verified

**Decision**: Port the three logo SVGs from
`landing-page/website/src/assets/images/logos/` into `docs-site/src/assets/` (for
the Starlight `logo` config, which imports from `src/`) and reference `mark.svg`
for the splash hero image.

**Confirmed present, with verified viewBox + fill mechanism**:

| Asset | Source file | viewBox | Fill mechanism (VERIFIED) |
| ----- | ----------- | ------- | ------------------------- |
| Wordmark (dark) | `logo.svg` | `0 0 1956 287` | inline `style="fill:#111827"` ×9 (text) + `fill:#dc143c` ×1 (mark) |
| Wordmark (light) | `logo-light.svg` | `0 0 1956 287` | inline `style="fill:#ffffff"` ×9 (text) + `fill:#dc143c` ×1 (mark) |
| Logomark / icon | `mark.svg` | `0 0 1250 1041` | attribute `fill="#111827"` + `fill="#dc143c"` |

**Important fill-mechanism finding**: the two wordmarks encode their colors with the
CSS `style="fill:#…"` property (not the `fill=` attribute), whereas `mark.svg` uses
the `fill=` attribute. This matters because it means the wordmark colors are baked
in (they do not inherit `currentColor`), so the dark/light split is handled by
selecting the correct file via Starlight's `logo.light` / `logo.dark`, not by CSS.
Confirmed via byte-diff: `logo.svg` and `logo-light.svg` differ only in the 9
text-fill hex values (`#111827` ↔ `#ffffff`); the red mark `#dc143c` is identical
in both. All three values match brand-guide §3 exactly — no reconciliation needed.

**Starlight `logo` mapping** (Starlight imports logo assets from `src/`, so place
the two wordmarks under `docs-site/src/assets/`):
```
logo: {
  light: './src/assets/logo.svg',       // dark wordmark on the warm light surface
  dark:  './src/assets/logo-light.svg',  // white wordmark on the dark surface
  replacesTitle: true,
  alt: 'Racecraft',
}
```
`replacesTitle: true` swaps the plain-text title for the image but Starlight keeps
the `title` value as the accessible site name for assistive tech (FR-009).

**Splash hero image** (`mark.svg`): the landing `hero.image` frontmatter takes a
`{ light, dark }` pair. `mark.svg` is a single dark-shape (`#111827`) + red-accent
logomark with a transparent background, so it reads on both surfaces; if it reads
weak on the dark hero block during Implement, supply a light-shape variant. Since
the brand source ships only one `mark.svg`, the plan uses it for both `light` and
`dark` hero slots and flags the dark-surface legibility check as an Implement-time
acceptance item (the hero block is true-black per FR-013, where the `#111827` shape
edges may need a stroke/glow — verify visually, do not pre-build a second asset).

**Alternatives considered**: recolor wordmarks via CSS `currentColor` (rejected:
source bakes fills in `style=`, two-file approach is idiomatic Starlight and lower
risk).

---

## Decision 4 — Current docs-site config: where each brand hook attaches

**Source read**: `docs-site/astro.config.mjs` (51 lines).

Current Starlight config holds: `title: 'Racecraft Public Plugins'`,
`plugins: [starlightLinksValidator()]`, a `head` array with one
`<meta name="robots" content="noindex, nofollow">` (DOC-012 staging guard — leave
in place), and a four-group `sidebar`. **It has no `customCss`, no `logo`, no
`favicon`, and no font `head` links yet** — all four are net-new keys this slice adds.

Attachment points (all inside the single `starlight({ … })` call):
- `customCss: ['./src/styles/brand.css']` — net-new key; `src/styles/` does not
  exist yet and is created by this slice.
- `logo: { light, dark, replacesTitle, alt }` — net-new key (see Decision 3).
- `favicon: '/favicon.svg'` — net-new key (Starlight emits the base-prefixed link).
- `head: [ … ]` — **append** the font `<link rel="preload">` tags and any extra
  favicon/manifest/theme-color `<link>`/`<meta>` tags to the **existing** `head`
  array; do not replace the existing robots meta.

**Landing route file**: `docs-site/src/content/docs/index.mdx` exists (currently a
plain doc titled "Start", 2,035 bytes, standard article body with sidebar groups).
This slice **rewrites** it to `template: splash` + `hero` + `<CardGrid>`.

**`public/` directory**: `docs-site/public/` currently contains only `robots.txt`
(26 bytes). Fonts and favicons are added alongside it (Assumptions confirmed).

**Primary-CTA tutorial slug (RESOLVED)**: the getting-started / first-workflow
tutorial is `docs-site/src/content/docs/first-run.md` (front-matter `title: "First
Run"`; opening line: "Use this route after installing SpecKit Pro… The first
successful run…"). With `base: '/racecraft-plugins-public'` and
`trailingSlash: 'always'`, the resolved primary-CTA link is:

> **`/racecraft-plugins-public/first-run/`**

(The design concept called this "DOC-005 getting-started/first-workflow tutorial";
the live route that fulfils it is `first-run`.) The secondary CTA →
`https://github.com/racecraft-lab/racecraft-plugins-public` (FR-003). The
`starlight-links-validator` plugin will fail the build on a wrong internal slug, so
the primary CTA link is build-verified.

**Build/validate commands** (from `docs-site/package.json`, pnpm@10.25.0):
`pnpm --dir docs-site build` (Astro build; `validate:links` aliases it) and
`pnpm --dir docs-site validate` (= `reference:check && check && validate:links &&
validate:safe-aids && validate:quality && validate:smoke:preview`). Node >=22.12
required. Plan is design-only — these are NOT run in this phase.

---

## Decision 5 — Brand → Starlight `--sl-color-*` token map (light + dark)

**Decision**: Map the Racecraft palette onto Starlight's documented custom
properties in `src/styles/brand.css`. Accent = blue family (links/active nav);
red = punctuation only (mark / theme_color / hero CTA — never the nav accent,
FR-005). Link-sized brand-blue text uses the AA-safe `#2a6a99` (FR-006).

**Starlight token model**: Starlight derives link/active-nav color from the
`--sl-color-accent` ramp (`-low` / base / `-high`) and reading surfaces from the
`--sl-color-gray-*` + `--sl-color-bg*` scale. Tokens are set under `:root`
(dark is Starlight's default) and overridden under `:root[data-theme='light']`.
Values below are anchored to the brand guide and reconciled against the live
landing-page CSS (the AA-safe blue, the warm-neutral surfaces, the soft-dark
range).

### Light mode (`:root[data-theme='light']`)

| Starlight token | Value | Brand source / rationale |
| --------------- | ----- | ------------------------ |
| `--sl-color-accent-low` | `#d6e4f0` | tint of brand blue for subtle backgrounds |
| `--sl-color-accent` | `#3c89c6` | Brand Blue — non-text accent (focus ring, active nav block) |
| `--sl-color-accent-high` | `#2a6a99` | **AA-safe blue** for link-sized text (5.0:1 on white) — FR-006 |
| `--sl-color-text` | `#111827` | neutral-900 foreground |
| `--sl-color-text-accent` | `#2a6a99` | link text = AA-safe blue (FR-006) |
| `--sl-color-bg` | `#f1f0ec` | pantone-base page background (warm neutral) |
| `--sl-color-bg-nav`/`--sl-color-bg-sidebar` | `#f7f6f4` | pantone-lighter raised surface |
| `--sl-color-gray-7` (deepest surface tint) | `#eeecea` | pantone-medium |
| `--sl-color-hairline`/border | `#e8e7e3` | pantone-dark subtle border |
| `--sl-color-white` (high-contrast text) | `#111827` | (Starlight uses gray-1/white as strongest fg) |

### Dark mode (`:root`, Starlight default)

| Starlight token | Value | Brand source / rationale |
| --------------- | ----- | ------------------------ |
| `--sl-color-accent-low` | `#13283a` | deep blue tint for subtle dark backgrounds |
| `--sl-color-accent` | `#3c89c6` | Brand Blue base (active nav block) |
| `--sl-color-accent-high` | `#7cb3dd` | **lightened/desaturated** blue for link text on dark (AA on soft-dark) — design Q3 "desaturate accent slightly" |
| `--sl-color-text` | `#e6e6e6` | near-white body (not pure `#fff`) for comfort |
| `--sl-color-text-accent` | `#7cb3dd` | link text = lightened blue (AA on `#1a1a1a`) |
| `--sl-color-bg` | `#1a1a1a` | **soft dark-gray reading surface** (within `#121212`–`#1e1e1e`) — FR-013 / SC-004 |
| `--sl-color-bg-nav`/`--sl-color-bg-sidebar` | `#1f2937` | brand dark `card`/`sidebar` |
| `--sl-color-gray-6` (raised surface) | `#1e1e1e` | soft-dark raised |
| `--sl-color-hairline`/border | `rgba(255,255,255,0.10)` | brand dark border |
| `--sl-color-white` (strongest fg) | `#ffffff` | headings on dark |

**Red as punctuation (both modes, NOT a `--sl-color-accent`)**: brand red
`#dc143c` is applied only via (a) the logo mark (baked into the SVGs), (b) the
`theme_color` in `site.webmanifest`, and (c) a scoped hero primary-CTA / hero-block
treatment in `brand.css` targeting only the splash hero (FR-005). It is never wired
into `--sl-color-accent`.

**Hero block true-black (FR-013)**: the decorative splash hero block uses GTO90
`#0a0a0a` (true black) — scoped to the hero only via a `.hero` / splash selector in
`brand.css`. The rest of dark mode stays on the `#1a1a1a` soft-dark surface. This is
the single sanctioned use of true black (SC-004).

**Contrast cross-check (the AA pairs that gate SC-003)**:
- Light link text `#2a6a99` on `#f1f0ec` / `#ffffff` → ≥ 5.0:1 (brand guide states
  5.0:1 vs white; warm-neutral `#f1f0ec` is marginally lighter → ≥ that). **AA ✅**
- Dark link text `#7cb3dd` on `#1a1a1a` → high-luminance blue on soft-dark, ample
  AA margin. **AA ✅** (exact ratio recorded as Implement verification evidence per
  the PR packet requirement).
- Body `#111827` on `#f1f0ec` (light) and `#e6e6e6` on `#1a1a1a` (dark) → both well
  above AA. **AA ✅**

**Rationale**: Mapping to Starlight's own custom properties (rather than restyling
components) is the documented, lowest-LOC, theme-consistent way to rebrand and keeps
DOC-016 (per-component restyle) cleanly out of scope. The AA-safe-blue-for-text /
brand-blue-for-non-text split is exactly the landing-page's own resolution of the
raw `#3c89c6` being only ~3.75:1.

**Alternatives considered**: restyle individual Starlight components / override
component CSS (rejected: that is DOC-016, and violates the surgical-edit constraint);
use brand blue `#3c89c6` for link text directly (rejected: fails AA at link size —
the whole reason `#2a6a99` exists).

### `@font-face` + font-token plan (FR-007 / FR-008)

In `brand.css`, declare five `@font-face` blocks (one per ported woff2), each with
`font-display: swap` and a Latin `unicode-range` is **not** added (files are already
subset; adding a range is cosmetic and skipped for KISS). Then point Starlight's
font tokens at the families with a system fallback first in each stack (so text is
visible immediately on font-load failure — Edge Case "fonts fail to load"):
- `--sl-font` (body/UI) → `"Geist", system-ui, sans-serif`
- `--sl-font-mono` (code) → `"Fira Code", ui-monospace, monospace`
- Display (H1/H2/buttons/nav) → `"Space Grotesk", system-ui, sans-serif` applied to
  heading selectors (Starlight has no separate display token, so headings get the
  Space Grotesk stack in `brand.css`).

Preload (in the config `head` array, base-path-prefixed `href`):
`space-grotesk-700.woff2` + `geist-400.woff2`, each `rel="preload" as="font"
type="font/woff2" crossorigin`.

---

## Open questions remaining after this research (deferred to Implement, by design)

- **Exact hero copy** (headline, tagline, 3 card titles/blurbs) — direction locked
  (plain-English, anti-hype value prop for spec-driven development; brand-guide §6
  verbal-tone reference), wording authored at Implement. Not a blocker.
- **Dark-hero `mark.svg` legibility** — verify the `#111827` logomark reads on the
  `#0a0a0a` hero block at Implement; add a light-shape variant only if it reads weak
  (do not pre-build). Not a blocker.
- **Lab grid/dot texture** — omit from the docs landing unless the page reads plain
  at Implement (Assumptions). Not a blocker.
- **Manifest icon base-path** — leave root-absolute vs base-prefix the manifest icon
  `src` values; decided at Implement when wiring the `<link>` tags (the head-tag
  hrefs must carry the `/racecraft-plugins-public` base prefix regardless).

All four are intentionally Implement-phase authoring/verification items, not
unresolved design unknowns. The plan therefore carries zero blocking clarification
markers — every design decision above is resolved against real file evidence.
