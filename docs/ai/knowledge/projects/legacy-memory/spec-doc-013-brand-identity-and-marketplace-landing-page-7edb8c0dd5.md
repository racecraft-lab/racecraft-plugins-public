---
type: "speckit-legacy-memory-record"
title: "DOC-013 Brand Identity and Marketplace Landing Page"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-7edb8c0dd566c001"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-013 Brand Identity and Marketplace Landing Page

[Source: specs/doc-013-brand-identity-marketplace-landing]

### Summary

Applied the Racecraft visual identity to the `docs-site/` Astro + Starlight site
and turned the stock-Starlight home route into a real marketplace landing page —
brand colors, typography, wordmark/logo, and favicons applied consistently across
light and dark mode while staying WCAG AA accessible. Merged via PR #246
(`6a0516ff`).

### User Stories

- **US1 (P1) — Branded marketplace landing page**: A visitor on the docs home
  route sees a splash-style landing (logo/mark, benefit-led headline, plain-English
  value prop, ~3 value-prop cards, one primary CTA to the getting-started/first-run
  tutorial, one secondary "View on GitHub" CTA) rather than a generic doc article,
  and understands the product and where to start without scrolling — on desktop and
  mobile.
- **US2 (P2) — Consistent, accessible site-wide brand identity**: Every route
  (landing or interior) carries the brand accent on links/active-nav, the brand
  display/body/mono typefaces, the header wordmark, and the favicon set, coherent
  in light and dark mode, with all text/interactive elements meeting WCAG AA.

### Functional Requirements (highlights)

- Home route renders as a Starlight-native `template: splash` landing (no bespoke
  components); the above-the-fold set {logo, benefit headline, value prop, primary
  CTA} fits the first screen on desktop and mobile (FR-001/001a/002).
- Exactly one primary CTA (→ first-run tutorial) + one visually-subordinate
  secondary CTA (→ GitHub); no competing CTAs (FR-003/003a). 2–4 anti-hype
  value-prop cards, 3 by default (FR-004/004a).
- Palette mapped to Starlight `--sl-color-*`: blue accent for links/active-nav;
  red `#dc143c` reserved as punctuation (logo, theme-color, hero CTA fill) and
  **never** failing normal-size text; AA-safe `#2a6a99` link text (FR-005/005a/006).
- Five self-hosted woff2 faces only (Space Grotesk 400/700, Geist 400/600, Fira
  Code regular) with `font-display: swap`; only the two above-the-fold faces
  (Space Grotesk 700 + Geist 400) preloaded, each with `crossorigin` (FR-007/008).
- Light/dark wordmark in header (`replacesTitle`, accessible name preserved), brand
  favicon set + theme color, logomark hero image with explicit `alt` (FR-009/010/011).
- Dark reading surface is soft `#1a1a1a` (true black `#0a0a0a` scoped to the hero
  block only); near-white `#e6e6e6` dark body text; visible focus ring `#3c89c6`
  ≥3:1 both modes; reduced-motion respected (FR-013/014/014a/015).

### Key Entities

Brand color token set (red/blue/AA-safe blue/warm neutrals → accent/link/surface/
theme roles); brand typeface set (display/body/mono + shipped weights); brand logo
assets (light/dark wordmark, logomark, favicon set); landing-page content (hero
headline, value-prop, CTA targets, ~3 card titles/blurbs).

### Success Criteria

First-time comprehension above the fold on desktop and mobile (SC-001); 100% of
routes carry brand accent/typefaces/wordmark/favicon in both modes (SC-002); 100%
of brand-accent text/interactive elements meet WCAG AA against an enumerated ratio
table with red only in passing patterns (SC-003); soft-dark reading surface (SC-004);
no invisible-text font flash + lean local 5-woff2 set with 2 preloads (SC-005);
CTAs resolve with no broken links (SC-006); within reviewability budget, no
out-of-scope leakage (SC-007); docs-site build/validation pass + reduced-motion
honored (SC-008).

### Cleanup Note

Archived into project memory on 2026-06-24 (PR #246, `6a0516ff`). The active
`specs/doc-013-brand-identity-marketplace-landing/` folder was removed from
`specs/**` in the post-merge cleanup; only `specs/.gitkeep` remains. Recovery
commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-24-doc-013-post-merge-hygiene.md`.
