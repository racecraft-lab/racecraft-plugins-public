---
topic: "DOC-013 — Brand identity and marketplace landing page"
date: 2026-06-23
source-input: "interactive-documentation-technical-roadmap.md (DOC-013) + brand audit of landing-page/website"
question-count: 6
mode: setup
spec-id: DOC-013
---

# Design Concept — DOC-013: Brand identity and marketplace landing page

Apply Racecraft visual identity to the speckit-pro docs site (Astro + Starlight
at `docs-site/`) and turn the stock-Starlight landing route into a real
marketplace landing page. Brand source values are captured in the companion
**[brand-guide.md](../../../../specs/doc-013-brand-identity-marketplace-landing/brand-guide.md)**,
ported from the sibling `landing-page/website` project. Every recommended answer
below was researched against Starlight docs (Context7) and accessibility/UX
best-practice sources (Tavily) before being offered.

## Goals

- Map the Racecraft brand palette to Starlight tokens with **blue as the
  site-wide accent** (links/active nav) and **red reserved as punctuation**
  (logo mark, `theme_color`, hero CTA). Use the AA-safe blue `#2a6a99` (5.0:1)
  for link-sized text.
- Build the landing route with **Starlight's native `template: splash` + `hero`
  frontmatter + a CardGrid** of ~3 value-prop cards — no custom components.
- **Dark mode uses a soft dark-gray reading surface** (Starlight default /
  `#121212`–`#1e1e1e` range) with brand accent layered on; true-black GTO90
  `#0a0a0a` is reserved for the decorative hero block only.
- Self-host a **lean weight set (~5–6 woff2)**: Space Grotesk 400/700, Geist
  400/600, Fira Code 400 — Latin-subset, `font-display: swap`, preload only
  Space Grotesk 700 + Geist 400.
- **Wordmark in the nav** (light/dark variants, `replacesTitle: true`, title
  kept for screen readers) and the **logomark `mark.svg` as the splash hero
  image** (light/dark variants).
- Hero **primary CTA → getting-started / first-workflow tutorial** (DOC-005),
  secondary CTA → View on GitHub; copy is a plain-English, anti-hype value prop
  for spec-driven development.
- Ship as a **single vertical slice** (estimator: 395 LOC, 1 slice, status ok;
  reviewability setup gate: within budget).

## Non-goals

- Per-component restyle beyond tokens — component-level a11y fixes are **DOC-016**.
- Performance budget / Lighthouse CI — **DOC-017** (DOC-013 keeps payload lean
  to leave headroom, but does not own the budget).
- Verbal voice / ELI5 tone system — **DOC-019**. Verbal-tone notes in the brand
  guide are reference only.
- Custom domain / base-path cutover — **DOC-012** (the launch gate).
- Porting the landing-page's animated hero or full weight range / true-black
  dark surface (rejected on a11y + budget grounds during the interview).

## Design Tree (Q&A log)

### Q1 — Site-wide accent color
**Recommended:** Blue accent (AA-safe `#2a6a99`), red as punctuation.
**Basis:** Starlight's `--sl-color-accent` styles links/active nav and defaults
to blue/indigo; WebAIM/Section508/AFixt — blue ~8.6:1 vs red ~4:1 on white, and
best practice reserves bold/bright colors (red) for CTAs; the landing-page
already made `#2a6a99` because raw `#3c89c6` is only ~3.75:1.
**User chose:** Blue accent (AA-safe), red as punctuation. ✅

### Q2 — Landing route build approach
**Recommended:** Native `template: splash` + `hero` frontmatter + CardGrid.
**Basis:** Starlight ships splash/hero/CardGrid natively (zero custom
components, inherits tokens, accessible by default, lowest LOC); CRO research
(Prismic/CXL/2026 conversion study) — benefit headline + 1 primary/1 secondary
CTA + ~3 scannable value points maps onto splash + CardGrid.
**User chose:** Native splash + hero + CardGrid. ✅

### Q3 — Dark-mode reading surface
**Recommended:** Soft dark-gray surface + brand accent; reserve true-black for
the hero block only.
**Basis:** Material Design / Smashing / NN-g / WebAIM all advise against pure
black reading surfaces — 21:1 contrast causes halation for the ~47–50% with
astigmatism plus eye fatigue; recommended `#121212`–`#1e1e1e`. Porting GTO90
`#0a0a0a` would work against DOC-016's contrast goals.
**User chose:** Soft dark-gray surface + brand accent. ✅

### Q4 — Self-hosted font weights
**Recommended:** Lean set (~5–6 weights): Space Grotesk 400/700, Geist 400/600,
Fira Code 400.
**Basis:** web.dev / DebugBear / self-hosting guides — ship only weights
actually used (~3–4), Latin-subset, WOFF2, `font-display: swap`, preload only
critical above-the-fold files. Shipping all 13 bloats payload and undercuts
DOC-017.
**User chose:** Lean set (~5–6 weights). ✅

### Q5 — Logo & hero imagery
**Recommended:** Wordmark in nav (light/dark, `replacesTitle: true`) + logomark
`mark.svg` as the splash hero image.
**Basis:** Starlight `logo` takes `{ light, dark, replacesTitle, alt }` and
keeps the title text for screen readers when `replacesTitle` is set (NN-g / W3C
— the header logo is a functional home link needing an accessible name); uses
all three brand assets idiomatically.
**User chose:** Wordmark in nav + logomark hero. ✅

### Q6 — Hero primary CTA destination
**Recommended:** Getting-started / first-workflow tutorial (DOC-005); secondary
→ View on GitHub.
**Basis:** CRO research — one benefit-led primary CTA + one secondary; for dev
tools the fastest 'it works' path (a guided tutorial) converts better than
dropping newcomers at a raw install command.
**User chose:** Getting-started / first-workflow tutorial. ✅

### Slice-sizing branch (advisory)
Size signals: 2 user stories, ~6 files, ~7 FRs, net-new. Shared estimator →
`{estimated_loc: 395, suggested_slices: 1, status: "ok"}`. Reviewability setup
gate → within budget (warn only on primary-surface count, not size). The work is
one thin vertical slice — brand tokens + fonts + logo + landing hero delivered
end-to-end. **No split.** Advisory note only.

## Open Questions

- **Exact hero copy** (headline, tagline, 3 card titles/blurbs) is deferred to
  the Specify/Implement phases — direction is locked (plain-English, anti-hype
  value prop for spec-driven development), wording is not. Draft against the
  brand guide's verbal-tone section.
- **Font subsetting/sourcing mechanics** — whether to copy the landing-page's
  existing subset woff2 verbatim or re-subset to Latin; resolve at Plan based on
  what `landing-page/website/public/fonts/` already ships.
- **Whether the lab grid/dot texture** appears on the docs landing — optional in
  the brand guide; default to omitting unless it reads as plain at implement.

## Recommended Next Step

Run the autopilot on the populated workflow file:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/DOC-013-workflow.md
```

Consult `specs/doc-013-brand-identity-marketplace-landing/brand-guide.md` for exact
token values throughout Plan and Implement.
