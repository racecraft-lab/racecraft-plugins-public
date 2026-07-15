---
type: "speckit-legacy-memory-record"
title: "Brand identity and marketplace landing page"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-cb210d8354704ce9"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Brand identity and marketplace landing page

[Source: specs/doc-013-brand-identity-marketplace-landing]

- **Feature**: Brand identity and marketplace landing page
- **Roadmap ID**: DOC-013
- **Branch**: `doc-013-brand-identity-marketplace-landing`
- **Spec path**: `specs/doc-013-brand-identity-marketplace-landing/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/246
- **Merge commit**: `6a0516ffef30e63b0f00347aa37463bdc1396d30`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: N/A (PR Checks green at merge: `validate-plugins`, `validate-pr-title`, `validate-docs`)
- **Argos build/review URL**: N/A (no visual-regression service; WCAG AA contrast evidence is the enumerated foreground/background ratio table in the PR packet)
- **Metadata gates**: `validate-pr-title=pass`, `validate-plugins=pass`, `validate-docs=pass`
- **Artifact manifest**: N/A (binary brand assets — 5 woff2, 10 favicon/manifest files, 3 logo SVGs — committed verbatim under `docs-site/public/` and `docs-site/src/assets/`)
- **Task completion**: 15 / 16 tasks checked (T016 "assemble the PR review packet" was completed via the merged PR #246 body but left unchecked in tasks.md)
- **Archived**: 2026-06-24
- **Status**: Completed

### Summary

DOC-013 applied the Racecraft visual identity to the `docs-site/` Astro 6.4.6 +
Starlight 0.40.0 site and converted the stock-Starlight home route into a real
marketplace landing page. A single `brand.css` maps the Racecraft palette onto
Starlight's `--sl-color-*` tokens for light and dark mode (blue accent for
links/active-nav, AA-safe `#2a6a99` link text, red `#dc143c` reserved as
punctuation — never as failing normal-size text, soft dark-gray `#1a1a1a`
reading surface with true black `#0a0a0a` scoped to the hero block only),
declares five self-hosted woff2 `@font-face`s with `font-display: swap`
(Space Grotesk 400/700, Geist 400/600, Fira Code regular), and points Starlight's
font tokens at those faces. `astro.config.mjs` wires `customCss`, the light/dark
wordmark `logo` (`replacesTitle`), the `favicon`, and two above-the-fold font
preloads (Space Grotesk 700 + Geist 400, each with `crossorigin="anonymous"`).
`index.mdx` became a Starlight-native `template: splash` + `hero` + `<CardGrid>`
landing with the logomark hero image, a benefit-led headline, ~3 anti-hype
value-prop cards, one primary CTA to `/racecraft-plugins-public/first-run/`, and
a subordinate secondary CTA to the GitHub repo. WCAG AA contrast is met in both
modes (enumerated ratio table recorded in the PR packet); reduced-motion is
respected. Brand assets were ported verbatim from the sibling `landing-page/website`
project. Per-component restyle (DOC-016), performance/Lighthouse budget (DOC-017),
verbal-voice/tone system (DOC-019), and domain/base-path cutover (DOC-012) were
explicitly deferred.

Post-merge review (Copilot) caught three issues fixed on-branch before merge: the
PWA manifest icon `src` values were base-path-prefixed (GitHub Pages project page),
the font preloads use explicit `crossorigin="anonymous"` (not a boolean), and a
stale heading-font-stack comment was corrected.

### Canonical Artifacts

- `docs-site/src/styles/brand.css` (NEW — token map + 5 `@font-face` + font tokens + scoped red/hero-block + focus ring + reduced-motion)
- `docs-site/astro.config.mjs` (MODIFIED — `customCss`, `logo`, `favicon`, font-preload/favicon/theme `head` tags)
- `docs-site/src/content/docs/index.mdx` (MODIFIED — `template: splash` + hero + CardGrid landing)
- `docs-site/src/assets/{logo.svg, logo-light.svg, mark.svg}` (NEW — wordmark + logomark)
- `docs-site/public/{favicon.svg, favicon.ico, favicon-16x16.png, favicon-32x32.png, favicon-32x32-light.png, favicon-48x48.png, apple-touch-icon.png, android-chrome-192x192.png, android-chrome-512x512.png, site.webmanifest}` (NEW — ported)
- `docs-site/public/fonts/{space-grotesk-400, space-grotesk-700, geist-400, geist-600, fira-code-regular}.woff2` (NEW — ported)

### Recovery Commands

```text
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/spec.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/plan.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/tasks.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/research.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/data-model.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/quickstart.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/brand-guide.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/SPEC-MOC.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:docs/ai/specs/.process/DOC-013-workflow.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:docs/ai/specs/.process/DOC-013-design-concept.md
git checkout 6a0516ffef30e63b0f00347aa37463bdc1396d30 -- specs/doc-013-brand-identity-marketplace-landing
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-24-doc-013-post-merge-hygiene.md`.

---
