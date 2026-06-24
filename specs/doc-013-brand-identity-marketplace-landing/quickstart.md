# Quickstart / Validation Guide: DOC-013

**Branch**: `doc-013-brand-identity-marketplace-landing`

Runnable validation scenarios that prove the brand pass + marketplace landing
page works end-to-end. Entity field definitions live in
[data-model.md](./data-model.md); design rationale + the token map live in
[research.md](./research.md). This guide is a run/verify checklist, not
implementation code.

## Prerequisites

- Node **>=22.12** (the design uses nvm `v22.22.2`).
- pnpm **10.25.0** (declared in `docs-site/package.json` `packageManager`).
- Brand source assets available (already confirmed present) at
  the sibling `landing-page/website` checkout (`public/` and `src/assets/images/logos/`).
- Run all commands from the worktree root
  `.worktrees/doc-013-brand-identity-marketplace-landing`.

## Setup (what Implement produces)

1. Copy 5 woff2 → `docs-site/public/fonts/` (see data-model Entity 2).
2. Copy 10 favicon/manifest files → `docs-site/public/` (Entity 3; do not touch
   the existing `robots.txt`).
3. Copy 3 logo SVGs → `docs-site/src/assets/` (Entity 3).
4. Create `docs-site/src/styles/brand.css` (token map + `@font-face` + font tokens
   + scoped red/hero-block rules + reduced-motion guard).
5. Edit `docs-site/astro.config.mjs` (add `customCss`, `logo`, `favicon`; append
   font preload + favicon/theme-color tags to the existing `head` array).
6. Rewrite `docs-site/src/content/docs/index.mdx` to `template: splash` + `hero` +
   `<CardGrid>` (Entity 4).

## Primary validation — full gate

```bash
pnpm --dir docs-site validate
```

Expected: passes. This runs, in order, `reference:check`, `astro check`,
`validate:links` (= `astro build`, which includes `starlight-links-validator`),
`validate:safe-aids`, `validate:quality`, and `validate:smoke:preview`
(Playwright). The **link validator** is the automated gate for SC-006 — a wrong
primary-CTA slug fails the build here.

## Scenario validations (map to acceptance scenarios + success criteria)

| # | What to check | How | Pass condition | Traces |
| - | ------------- | --- | -------------- | ------ |
| 1 | Home route is a splash landing | Load `/racecraft-plugins-public/` | Mark + headline + value-prop + primary CTA + secondary CTA visible; not a sidebar article | FR-001/002, AS S1#1, SC-001 |
| 2 | Primary CTA target | Click primary CTA | Resolves to `/racecraft-plugins-public/first-run/` | FR-003, SC-006, VR-15 |
| 3 | Secondary CTA target | Click secondary CTA | Resolves to GitHub repo | FR-003, SC-006 |
| 4 | ~3 value-prop cards | Scan hero card area | ~3 plain-English, anti-hype cards | FR-004, AS S1#3 |
| 5 | Light-mode brand | Any route, light mode | Blue accent on links/active-nav; Space Grotesk/Geist/Fira Code; dark wordmark in header; brand favicon in tab | FR-005/007/009/011, SC-002 |
| 6 | Dark-mode brand | Any route, dark mode | Soft dark-gray surface (`#1a1a1a`, NOT pure black); light wordmark; accent + type applied | FR-012/013, AS S2#2, SC-004 |
| 7 | Theme toggle, no wrong-asset flash | Toggle light↔dark | Correct light/dark wordmark + accent each time; no flash of the wrong theme's assets | AS S2#3 |
| 8 | Red is punctuation only | Inspect links/nav vs mark/CTA | Red only on logo mark, `theme_color`, hero CTA; never the nav/link accent | FR-005, VR-1 |
| 9 | WCAG AA contrast | Measure link + body text vs bg, both modes | Link `#2a6a99` (light) / `#7cb3dd` (dark) ≥ AA; body ≥ AA — **record the measured ratios as PR evidence** | FR-006/014, SC-003 |
| 10 | Font-load resilience | Throttle/deny fonts | Text stays visible via system fallback (`font-display: swap`); layout intact | FR-008, SC-005, Edge "fonts fail" |
| 11 | Lean set + local only | Inspect `public/fonts/` + network | Exactly 5 woff2; zero external font-host request | FR-007/008, SC-005, VR-5 |
| 12 | Preload critical faces | View source `<head>` | `space-grotesk-700` + `geist-400` preloaded, base-path-prefixed | FR-008, VR-7 |
| 13 | Header logo a11y + home link | Inspect header | Accessible name "Racecraft" present; logo links home | FR-009, VR-9 |
| 14 | Narrow viewport | Mobile width | Hero, cards, CTAs readable, no horizontal scroll | AS S1#4, Edge "narrow" |
| 15 | Reduced motion | `prefers-reduced-motion: reduce` | Entrance animation suppressed/reduced | FR-015, SC-008, AS S2#5 |
| 16 | Build/validate green | `pnpm --dir docs-site validate` | All sub-checks pass | SC-008 |

## Reviewability check (SC-007)

```bash
# from worktree root — projects production LOC from the plan's Declared File
# Operations block (binary assets excluded by the estimator):
bash speckit-pro/scripts/estimate-reviewable-loc.sh \
  specs/doc-013-brand-identity-marketplace-landing/plan.md 2>/dev/null || true
```

Expected: within budget (~80 reviewable CSS LOC; 1–2 primary production files;
6–8 total text/config files plus binary assets). No scope from DOC-016 / DOC-017 /
DOC-019 / DOC-012.

## Out of scope (do NOT validate here — separate specs)

Per-component a11y restyle → **DOC-016**. Performance/Lighthouse budget →
**DOC-017**. Verbal-voice/tone system → **DOC-019**. Custom domain / base-path
cutover → **DOC-012**.
