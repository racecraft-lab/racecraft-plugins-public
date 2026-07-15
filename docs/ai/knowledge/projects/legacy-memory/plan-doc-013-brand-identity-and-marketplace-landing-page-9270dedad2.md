---
type: "speckit-legacy-memory-record"
title: "DOC-013 Brand Identity and Marketplace Landing Page"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-9270dedad2948c37"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-013 Brand Identity and Marketplace Landing Page

[Source: specs/doc-013-brand-identity-marketplace-landing]

### Dependencies and Environment

- **Runtime/build**: Docs-site JavaScript ESM on Node >=22.12 (nvm `v22.22.2`);
  CSS + Markdown/MDX. No application source language.
- **Primary dependencies**: Astro 6.4.6, Starlight 0.40.0, `starlight-links-validator`
  0.24.1 (all existing); pnpm 10.25.0 via `pnpm --dir docs-site …`. **No new runtime
  dependency** — brand fonts copied verbatim (no subsetting toolchain added).
- **Storage**: checked-in repository files only (CSS, MDX, SVG, woff2, favicon
  PNG/ICO, `site.webmanifest`). No database, browser storage, or runtime state.
- **Target**: static GitHub Pages site under `base: '/racecraft-plugins-public'`,
  `trailingSlash: 'always'`; modern browsers, light + dark mode.

### Architecture / Structure

All changes live under the existing `docs-site/` tree. One new stylesheet
(`src/styles/brand.css`) carries the bulk of the reviewable LOC; `astro.config.mjs`
is edited to wire `customCss`/`logo`/`favicon`/`head` preload+favicon+theme tags;
`src/content/docs/index.mdx` is rewritten to a Starlight-native `template: splash`
+ `hero` + `<CardGrid>`. Brand assets are ported verbatim from `landing-page/website`:
3 logo SVGs → `src/assets/`, 5 woff2 → `public/fonts/`, 10 favicon/manifest files →
`public/` (alongside the existing `robots.txt`, untouched). Two production text
files + one config file + 18 binary assets; `src/styles/` is the only new subdir.

### Testing Strategy

`pnpm --dir docs-site validate` (Astro check + `starlight-links-validator` build +
safe-aids + docs-quality + Playwright smoke-preview) is the gate, run by CI
`validate-docs`. The repo deterministic suite `bash tests/speckit-pro/run-all.sh`
is unaffected (no `speckit-pro/` or `tests/` files touched). PR evidence includes
the build pass plus an enumerated WCAG AA contrast table (link text, body text,
non-text blue accent, focus ring, red punctuation) in both modes.

### Constitution Check

PASS. Principles I–III/N/A (no plugin manifest/script/version touched); IV pass
(docs-site validate is the gate, no Layer-4 owed); V pass (conventional, public-
readable title); VI pass (Starlight-native, no bespoke components, fonts copied
verbatim). Reviewability: ~80 reviewable CSS LOC + small MDX + config — within
budget; single vertical slice, no split. Deferred: DOC-016/017/019/012.

### Cleanup Notes

`specs/doc-013-brand-identity-marketplace-landing` was removed from active
`specs/**` in the post-merge cleanup; only `specs/.gitkeep` remains. Recovery
commands and provenance are recorded in the DOC-013 archive report.
