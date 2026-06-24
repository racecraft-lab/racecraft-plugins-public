# SpecKit Workflow: DOC-013 — Brand identity and marketplace landing page

**Template Version**: 1.0.0
**Created**: 2026-06-23
**Purpose**: Autopilot-ready workflow for applying Racecraft visual identity to the speckit-pro docs site and turning the landing route into a marketplace landing page.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/DOC-013-design-concept.md
```

The companion **brand guide** (exact tokens, fonts, logos, favicons) lives at:

```text
specs/doc-013-brand-identity-marketplace-landing/brand-guide.md
```

Re-read both before each phase. Every scoping decision below traces to a
researched (Context7 + Tavily) recommendation the maintainer accepted; the
design concept is the source of truth for any decision captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. Once autopilot begins,
> clarifications happen via `/speckit-clarify` and the consensus protocol —
> never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ⏳ Pending | |
| Clarify | `/speckit-clarify` | ⏳ Pending | Optional but recommended |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Run for each domain |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

Verify alignment with the project constitution (`.specify/memory/constitution.md`) if present.

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Simplicity / YAGNI | Use Starlight-native features over custom components | Code review |
| Accessibility | WCAG AA contrast in both light and dark | Color contrast check; `pnpm --dir docs-site validate` |
| Surgical edits | Touch only docs-site brand surfaces | Diff review |

**Constitution Check:** ✅ / ❌ (mark before proceeding to G1)

### Project Commands

| Command | Value |
|---------|-------|
| BUILD | `pnpm --dir docs-site build` |
| FULL_VERIFY | `pnpm --dir docs-site validate` (Astro check + links validator) |
| SMOKE | `pnpm --dir docs-site validate:smoke` (Playwright, if present) |
| REPO_TESTS | `bash tests/speckit-pro/run-all.sh` |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-013 |
| **Name** | Brand identity and marketplace landing page |
| **Branch** | `doc-013-brand-identity-marketplace-landing` |
| **Dependencies** | DOC-002 (unified landing page and IA shell) |
| **Enables** | DOC-016 (contrast hardening), public launch |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] `docs-site/public/` exists with the ported favicon set + `site.webmanifest`.
- [ ] `docs-site/src/styles/brand.css` maps brand colors to Starlight `--sl-color-*` tokens for light **and** dark, wired via `customCss`; blue is the accent, red is punctuation, dark surface is soft gray.
- [ ] Space Grotesk / Geist / Fira Code are self-hosted (lean weight set), Latin-subset, `font-display: swap`, with `<link rel="preload">` for the critical files; Starlight font tokens set.
- [ ] `logo` (light/dark wordmark, `replacesTitle`) and `favicon` set in the Starlight config.
- [ ] `docs-site/src/content/docs/index.mdx` uses `template: splash` + a branded hero (logomark image, value-prop, primary CTA → getting-started tutorial, secondary → GitHub) + a CardGrid of ~3 value points.
- [ ] `pnpm --dir docs-site validate` passes; both modes meet WCAG AA.

---

## Phase 1: Specify

**When to run:** Start of the feature. Focus on **WHAT** and **WHY**. Output: `specs/doc-013-brand-identity-marketplace-landing/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Brand identity and marketplace landing page (DOC-013)

### Problem Statement
The speckit-pro docs site (Astro + Starlight, docs-site/) is stock Starlight —
no customCss, logo, favicon, fonts, or public/ dir; default blue/lavender accent,
system font, no logo, and the landing route renders as a generic doc page rather
than a marketplace entry point. A full brand kit already exists in the sibling
landing-page/website project and is captured in
specs/doc-013-brand-identity-marketplace-landing/brand-guide.md.

### Goal
Apply Racecraft visual identity to the docs site and turn the landing route into
a real marketplace landing page.

### Users
Visitors evaluating the speckit-pro plugin marketplace, and existing users
navigating the docs.

### User Stories
- [US1] As a visitor, I land on a branded marketplace page (logo, hero, value
  prop, clear primary CTA) that tells me what speckit-pro is and how to start,
  not a generic doc page.
- [US2] As any reader, the whole docs site carries Racecraft brand colors,
  typography, logo, and favicons consistently in both light and dark mode, and
  remains accessible (WCAG AA).

### Decisions locked during grill-me (see design concept)
- Accent = blue family (AA-safe #2a6a99 for link-text); red #dc143c reserved for
  logo mark, theme_color, and hero CTA.
- Landing route uses Starlight-native `template: splash` + `hero` frontmatter +
  CardGrid (no custom components).
- Dark mode uses a soft dark-gray reading surface (#121212–#1e1e1e / Starlight
  default), NOT GTO90 true-black #0a0a0a; true-black reserved for the hero block.
- Self-host a lean weight set: Space Grotesk 400/700, Geist 400/600, Fira Code
  400; Latin-subset; font-display: swap; preload Space Grotesk 700 + Geist 400.
- Wordmark in nav (light/dark, replacesTitle); logomark mark.svg as hero image.
- Hero primary CTA → getting-started / first-workflow tutorial (DOC-005);
  secondary → View on GitHub. Copy is plain-English, anti-hype.

### Constraints
- Brand values are fixed by the brand guide; verify against the live
  landing-page/website CSS if any value is ambiguous.
- Reviewability budget: ~80 reviewable CSS LOC, 1–2 production files, 6–8 total
  files plus binary font/favicon assets.

### Out of Scope
- Per-component restyle beyond tokens (DOC-016).
- Performance budget / Lighthouse CI (DOC-017).
- Verbal voice / ELI5 tone system (DOC-019).
- Custom domain / base-path cutover (DOC-012).
```

### Files Generated

- [ ] `specs/doc-013-brand-identity-marketplace-landing/spec.md`

---

## Phase 2: Clarify (Optional but Recommended)

Most ambiguity was resolved during grill-me. Seed Clarify from the design
concept's Open Questions only.

#### Session 1: Hero copy & content

```bash
/speckit-clarify Focus on landing-page content: exact hero headline/tagline, the 3 CardGrid value points, primary CTA label and target slug (getting-started/first-workflow tutorial, DOC-005), secondary CTA (GitHub). Keep the plain-English, anti-hype tone from the brand guide.
```

#### Session 2: Font sourcing & token wiring

```bash
/speckit-clarify Focus on assets: whether to copy landing-page/website/public/fonts woff2 verbatim or re-subset to Latin; exact Starlight --sl-color-* and font token mapping for light vs dark; preload set; whether the lab grid/dot texture appears on the docs landing (default: omit).
```

---

## Phase 3: Plan

**Output:** `specs/doc-013-brand-identity-marketplace-landing/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Site: Astro 6.4.6 + Starlight 0.40.0 in docs-site/ (pnpm 10.25.0, `pnpm --dir docs-site ...`)
- Styling: brand.css mapped to Starlight `--sl-color-*` tokens, wired via customCss in astro.config.mjs
- Fonts: self-hosted woff2 under docs-site/public/fonts/, @font-face + <link rel=preload>
- Content: MDX landing route with `template: splash` + `hero` frontmatter + CardGrid/Card

## Source of truth
- specs/doc-013-brand-identity-marketplace-landing/brand-guide.md (exact tokens, fonts, logos, favicons)
- Brand source files: landing-page/website/public/ and landing-page/website/src/assets/images/logos/

## Architecture Notes
- Accent → blue family; AA-safe #2a6a99 for link-sized text; red as punctuation.
- Dark mode: soft dark-gray surface (#121212–#1e1e1e), desaturate accent slightly; reserve true-black for the hero block only.
- Lean font weights: Space Grotesk 400/700, Geist 400/600, Fira Code 400; Latin-subset; font-display: swap; preload Space Grotesk 700 + Geist 400.
- logo: { light: ./logo.svg (dark wordmark), dark: ./logo-light.svg (white wordmark), replacesTitle: true, alt: 'Racecraft' }; favicon set from public/.
- Landing hero image = logomark mark.svg (light/dark); primary CTA → getting-started tutorial; secondary → GitHub.

## Constraints
- Stay within docs-site/ brand surfaces; do not restyle individual components (DOC-016) or chase a perf budget (DOC-017).
- `pnpm --dir docs-site validate` must pass; both modes WCAG AA.
```

---

## Phase 4: Domain Checklists

### Recommended domains (from grill-me design tree)

- **accessibility** — color contrast (light + dark), link/non-link contrast, logo alt text / replacesTitle screen-reader behavior, prefers-reduced-motion, halation avoidance in dark mode.
- **ux** — hero clarity, single primary CTA + one secondary, scannable value points, marketplace-entry-point reading.
- **performance** *(light touch — DOC-017 owns the budget)* — font payload (lean weights, subset, preload), no render-blocking, font-display: swap.

#### 1. accessibility Checklist

```bash
/speckit-checklist accessibility

Focus on DOC-013 requirements:
- Link text and accent meet WCAG AA in both light and dark (AA-safe #2a6a99 for link-sized text)
- Dark mode avoids pure-black reading surfaces (halation); uses #121212–#1e1e1e
- Logo is a functional home link with an accessible name (replacesTitle keeps title for screen readers); hero logomark has appropriate alt
- Hero/entrance animations respect prefers-reduced-motion
- Pay special attention to: contrast of red used as punctuation on the warm base
```

#### 2. ux Checklist

```bash
/speckit-checklist ux

Focus on DOC-013 requirements:
- Landing route reads as a marketplace entry point, not a doc page
- One benefit-led primary CTA (getting-started) + one secondary (GitHub), no competing CTAs
- ~3 scannable CardGrid value points, benefit-led copy
- Pay special attention to: plain-English anti-hype tone consistent with the brand guide
```

#### 3. performance Checklist

```bash
/speckit-checklist performance

Focus on DOC-013 requirements:
- Lean self-hosted font set, Latin-subset, woff2, font-display: swap
- Preload only critical above-the-fold files (Space Grotesk 700 + Geist 400)
- Pay special attention to: not regressing CWV ahead of DOC-017
```

---

## Phase 5: Tasks

**Output:** `specs/doc-013-brand-identity-marketplace-landing/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; reference FR-xxx and brand-guide values
- Dependency order: public/ assets (favicons, fonts) → brand.css tokens (light+dark) → astro.config wiring (customCss, logo, favicon, fonts) → landing hero (index.mdx splash) → validate
- Organize by user story (US1 landing page, US2 site-wide identity)

## Constraints
- One vertical slice (estimator: ~395 LOC, 1 slice). Do not split.
- Stay within docs-site/; binary assets ported from landing-page/website.
- Bound by Non-goals: no per-component restyle (DOC-016), no perf budget (DOC-017), no verbal tone (DOC-019).
```

---

## Atomicity Route

*Placeholder — filled by the autopilot after Tasks/G5 via the read-only classifier.*

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for destructive-migration/concurrency-sensitive changes. |
| **Signals** | | Decisive detector findings. |
| **Warnings** | | Release-safety warnings (empty when none). |

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-013-brand-identity-marketplace-landing
```

---

## Phase 6: Analyze

```bash
/speckit-analyze

Focus on:
1. Constitution alignment (simplicity, accessibility, surgical edits)
2. Coverage gaps — every FR and user story has tasks
3. Drift between the design concept's decisions (accent, dark surface, font weights, logo, CTA) and spec.md/plan.md/tasks.md — the design concept wins unless there is an explicit revision note
4. Consistency of file paths with docs-site/ structure
```

---

## Phase 7: Implement

```bash
/speckit-implement

## Approach
This is a visual/CSS + content spec; "tests" are the docs-site validators plus
manual visual verification in both light and dark mode.

For each task:
1. Apply the change using exact values from brand-guide.md
2. Run `pnpm --dir docs-site validate` (Astro check + links validator)
3. Visually verify light AND dark mode (contrast, logo variants, hero, fonts)
4. Confirm no per-component restyle leaked in (that's DOC-016)

### Pre-Implementation Setup
1. `pnpm --dir docs-site install` if needed (Node >=22.12)
2. Confirm `pnpm --dir docs-site validate` passes on the untouched site first
3. Port binary assets from landing-page/website/public/ (favicons, fonts) and src/assets/images/logos/ (wordmarks, mark)
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - public/ assets (favicons, fonts) | | | |
| 2 - brand.css tokens (light + dark) | | | |
| 3 - astro.config wiring (customCss, logo, favicon, fonts) | | | |
| 4 - landing hero (index.mdx splash + CardGrid) | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] `pnpm --dir docs-site validate` passes
- [ ] `pnpm --dir docs-site build` succeeds
- [ ] Light + dark mode visually verified; both meet WCAG AA
- [ ] `bash tests/speckit-pro/run-all.sh` (repo structural layers) passes
- [ ] PR created with a plain-English, conventional-commits title (e.g. `feat(docs-site): apply Racecraft brand identity and marketplace landing page`)

---

## Project Structure Reference

```
docs-site/
├── astro.config.mjs            # customCss, logo, favicon, fonts wiring
├── public/                     # NEW — favicons, site.webmanifest, fonts/
├── src/
│   ├── styles/brand.css        # NEW — brand tokens (light + dark)
│   └── content/docs/index.mdx  # landing route → splash + hero + CardGrid
specs/doc-013-brand-identity-marketplace-landing/
├── SPEC-MOC.md
├── brand-guide.md              # exact tokens / fonts / logos / favicons
└── spec.md, plan.md, tasks.md  # generated by the phases above
```
