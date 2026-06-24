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
| Specify | `/speckit-specify` | ✅ Complete | G1 pass — 0 `[NEEDS CLARIFICATION]`, 17 FRs, 8 SCs, 2 stories, 9 scenarios |
| Clarify | `/speckit-clarify` | ✅ Skipped | G1 clean (0 markers); open questions deferred by design — fonts→Plan, hero copy→Implement |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass — plan/research/data-model/quickstart, 0 markers, reviewability `pass` (~40 LOC), constitution ✅ |
| Checklist | `/speckit-checklist` | ✅ Complete | G4 pass — accessibility/ux/performance, 14 gaps fixed, 0 remaining, 0 unresolved (no consensus) |
| Tasks | `/speckit-tasks` | ✅ Complete | G5 pass — 16 tasks (T001–T016, 3 `[P]`), every FR covered, explicit verify tasks (validate/contrast/reduced-motion), 0 markers; route `one-navigable-PR` (no split) |
| Analyze | `/speckit-analyze` | ✅ Complete | G6 pass — 0 CRITICAL; no drift; values verified vs real filesystem; 2 non-blocking citation/prose items fixed by orchestrator; 0 unresolved (no consensus) |
| Implement | `/speckit-implement` | ✅ Complete | G7 pass — `validate` GREEN (incl. 20/20 Playwright smoke); all contrast AA; 1 cross-spec contract update (DOC-010 home `/` h1) |

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

**Constitution Check:** ✅ (G0, 2026-06-23) — DOC-013 is a docs-site change: plugin-structure (I), script-safety (II), and semver (III) principles are N/A (no plugin/script/version touched); test-coverage (IV) = docs-site validators + repo structural suite; conventional-commits (V) honored via `feat(docs-site):`; KISS/YAGNI (VI) honored (Starlight-native, single vertical slice). Baseline `bash tests/speckit-pro/run-all.sh --layer 1` → **1325/1325 passed**. Accessibility build-baseline (`pnpm --dir docs-site validate`) deferred to Phase 7 Pre-Implementation Setup per this workflow.

### Pre-Flight Record (2026-06-23, autopilot)

| Item | Value |
|------|-------|
| Branch / worktree | `doc-013-brand-identity-marketplace-landing` (worktree; non-numeric → `feature.json` pins the feature dir) |
| SpecKit CLI | specify 0.11.6 |
| PROJECT_COMMANDS | BUILD `pnpm --dir docs-site build` · FULL_VERIFY `pnpm --dir docs-site validate` · REPO_TESTS `bash tests/speckit-pro/run-all.sh` (auto-detect found none at repo root; docs-site has its own package.json — workflow values are authoritative) |
| PRESET_CONVENTIONS | `speckit-pro-reviewability` v1.0.0 (spec/plan/tasks templates resolve) |
| Extensions (enabled) | verify, verify-tasks, checkpoint, retrospective, speckit-utils, git, archive · (review, cleanup absent → post-tasks skipped) |
| Confidence gate mode | advisory (threshold 0.90) |
| Agent Teams | Path B (batched background subagents) — right-sized for a single slice |
| PROJECT_IMPLEMENTATION_AGENT | `speckit-pro:phase-executor` (no docs-site implementer in `.claude/agents/`); a11y-reviewer + performance-reviewer used for Phase-7 verification |
| Archive sweep | no-op — current target is the only spec in the worktree |
| SpecKit bug found + fixed | `.specify/scripts/bash/check-prerequisites.sh` lacked the `feature.json` branch-check bypass its siblings have (broke clarify/checklist/analyze/implement on `doc-`/`prsg-` branches). Fixed as its own PR off main (#245); applied locally via `skip-worktree` so it stays out of the DOC-013 brand PR. |
| Doctor (Phase 0) | Health **OK** — templates 5/5, scripts 6/6 executable + `bash -n` clean (incl. the fixed `check-prerequisites.sh`), 7 extensions enabled, worktree/branch confirmed. No blocking items. Benign note: `extensions.yml installed:` lists only archive+git while `.registry` (authoritative) shows all 7 — representation mismatch, not a defect. |

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

- [x] `specs/doc-013-brand-identity-marketplace-landing/spec.md` — 17 FRs, 8 SCs, 2 user stories (US1 P1 landing, US2 P2 site-wide), 9 acceptance scenarios, Reviewability Budget within budget (single slice), 0 clarification markers
- [x] `specs/doc-013-brand-identity-marketplace-landing/checklists/requirements.md` — spec quality checklist, all pass

---

## Phase 2: Clarify (Optional but Recommended)

Most ambiguity was resolved during grill-me. Seed Clarify from the design
concept's Open Questions only.

> **Clarify SKIPPED (G1 clean, 2026-06-23).** Specify returned **0
> `[NEEDS CLARIFICATION]` markers** — all ambiguity was resolved with informed
> defaults documented in the spec's Assumptions section. The two seeded sessions
> below target questions that are deferred **by design**, not spec-level
> ambiguities: hero copy (headline/tagline/card text) is authored during
> **Implement** against the brand guide's verbal-tone reference (direction
> locked, wording flexible — Assumption + FR-002/FR-004); font subset mechanics
> and the exact `--sl-color-*`/font token mapping are a **Plan**-phase
> investigation of the actual `landing-page/website/public/fonts/` files (the
> Plan prompt says so); the lab grid/dot texture defaults to omit. Running
> clarify-executors here would only confirm these deferrals and risk
> prematurely locking decisions Plan/Implement must make with file evidence.
> Spec also corrected one fact: `docs-site/public/` already exists (holds
> `robots.txt`) — assets are added alongside it.

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

### Plan Results (G3 ✅ — 2026-06-23)

Artifacts: `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (no `contracts/` — UI + Starlight config is the contract, validated by `pnpm --dir docs-site validate`). 0 `[NEEDS CLARIFICATION]`, no `[Gap]`/`[CRITICAL]`. Constitution v1.1.0 passes (I/II/III N/A; IV/V/VI pass). Reviewability estimator: `status: pass`, projected ~40 LOC, 21 file ops (19 NEW + 2 MODIFIED), single slice — no split.

**Resolved open questions (from real file investigation of `landing-page/website`):**
- **Fonts → COPY VERBATIM** (already small subset woff2; re-subsetting would add a `fonttools` dep — rejected on KISS/YAGNI + DOC-017). Port 5: `space-grotesk-400.woff2`, `space-grotesk-700.woff2` (preload), `geist-400.woff2` (preload), `geist-600.woff2`, **`fira-code-regular.woff2`** (source names mono `-regular`, not `-400`).
- **Assets present** — favicons/manifest (10) → `public/`; logos (3: `logo.svg` dark wordmark vbox `0 0 1956 287`, `logo-light.svg` white wordmark, `mark.svg` logomark vbox `0 0 1250 1041`) → `src/assets/`. Wordmarks bake fills via `style="fill:"` (not `currentColor`) → light/dark handled by Starlight `logo.light`/`logo.dark` file selection.
- **Primary CTA slug → `/racecraft-plugins-public/first-run/`** (`docs-site/src/content/docs/first-run.md`); secondary → `https://github.com/racecraft-lab/racecraft-plugins-public`. Link build-verified by `starlight-links-validator`.

**Token map (brand → `--sl-color-*`):**
- Light: `bg #f1f0ec`, `text #111827`, `accent #3c89c6` (non-text), `text-accent/accent-high #2a6a99` (AA link text ≥5.0:1), `accent-low #d6e4f0`.
- Dark (default): `bg #1a1a1a` (soft gray, not pure black), `text #e6e6e6`, `accent #3c89c6`, `text-accent/accent-high #7cb3dd` (lightened for AA-on-dark), `accent-low #13283a`; hero block true-black `#0a0a0a` scoped to splash only. Red `#dc143c` = punctuation only (mark / `theme_color` / hero CTA), never `--sl-color-accent`.

**File-by-file:** NEW `docs-site/src/styles/brand.css` (~80 CSS LOC: tokens light+dark, 5 `@font-face` swap, font-token assignments, scoped red/hero true-black, `prefers-reduced-motion` guard) · MODIFIED `docs-site/astro.config.mjs` (add `customCss`, `logo`, `favicon`; **append** preload + favicon/theme-color to existing `head`) · MODIFIED `docs-site/src/content/docs/index.mdx` (→ `template: splash` + hero + CardGrid ×3) · ported binary assets (`public/robots.txt` untouched).

**Deferred to Implement (by design):** hero copy + 3 card blurbs (direction locked: plain-English anti-hype); dark-hero `mark.svg` legibility on `#0a0a0a` (visual check, add light variant only if weak); lab grid/dot texture (omit unless plain); webmanifest icon `src` base-path.

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

### Checklist Results (G4 ✅ — 2026-06-23)

All three domains ran sequentially (checklist-executor: research → remediate → re-verify). **14 gaps found, 14 remediated, 0 remaining, 0 unresolved for consensus.** Every fix cited an authoritative source. Checklist files: `checklists/{accessibility,ux,performance}.md`.

- **accessibility** (6 gaps) — caught a real WCAG issue: **red `#dc143c` as small text FAILS AA** (4.38:1 on `#f1f0ec`, 3.97:1 on `#0a0a0a`). New **FR-005a** constrains red to passing patterns only (white-on-red fill 4.99:1, large/non-text ≥3:1, or logo-mark logotype exception — never small red text). Also: FR-006/FR-014 numeric AA thresholds; FR-010 hero `alt`; FR-013 soft-dark range + halation rationale; **FR-014a** visible focus indicator (ring `#3c89c6` = 3.30:1 light / 4.63:1 dark, both ≥3:1) + acceptance scenario US2.6.
- **ux** (6 gaps) — **FR-001a** above-the-fold element set {logo, benefit headline, value-prop, primary CTA}, holds on mobile; **FR-003a** exactly one primary + at-most-one *visually subordinate* secondary CTA (Starlight `hero.actions` `variant`); FR-002 tightened to benefit-led (outcome, not product name); **FR-004a** anti-hype made testable (no hype superlatives, no unexplained jargon, concrete over fluff). Sources: NN/g, CXL, Starlight docs.
- **performance** (2 gaps, light-touch) — **FR-007** mandates woff2 (prohibits TTF/OTF/WOFF; exactly 5 faces); **FR-008** adds preload *ceiling* (only Space Grotesk 700 + Geist 400; other 3 MUST NOT preload), `font-display: swap` on every `@font-face`, and `crossorigin` on each preload. **Scope boundary held** — no perf budget / CWV threshold added (those stay DOC-017). Sources: web.dev, MDN.

Requirements after Checklist: 17 base FRs + 5 sub-FRs (FR-001a/003a/004a/005a/014a) + 1 acceptance scenario (US2.6).

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

*Recorded by the autopilot after Tasks/G5 (2026-06-23) via the read-only classifier.*

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | Single navigable PR — not a split. |
| **Releasable** | `true` | No destructive migration / concurrency hazard. |
| **Signals** | `change-shape:modify-heavy` | Cohesive brand slice across a few files. |
| **Warnings** | (none) | — |

**Layer Plan:** `skipped` — route is not `split-PR`, so the PRSG-008 layer planner does not run. Ships as one navigable PR.

**Reviewability tasks-gate (advisory):** `status: block` but **size-only and a known coarse false positive** — the blocker is `total_files: 132 > 25`, where the tasks-gate counts path-tokens in `tasks.md` (18 binary font/favicon/logo assets — explicitly **non-reviewable** per the spec's Reviewability Budget — plus source/reference paths). `reviewable_loc: 640` is the coarse `tasks×40` heuristic and is only a warn (< 800 block). The **accurate plan-phase estimator** reported **40 reviewable LOC, `status: pass`, single slice**. Per the skill, a size-only tasks-gate block is **not** a manual re-slicing stop; the authoritative reviewability gate is the **PR-time `final-reviewability-backstop` (diff-mode)** on the real `origin/main...HEAD` diff, where binary assets don't count as reviewable LOC. **No re-slice; no `pr_marker_plan` (single-PR path).**

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-013-brand-identity-marketplace-landing
```

---

## Phase 6: Analyze

### Analyze Results (G6 ✅ — 2026-06-23)

Cross-artifact analysis (spec/plan/tasks/research/data-model/design-concept). **0 CRITICAL, 0 HIGH.** 100% FR coverage by substance, 2/2 stories, 0 ambiguity, 0 duplication. **No design-concept drift** — all four locked decisions preserved (blue accent + red-as-punctuation, soft-dark not true-black, Starlight-native splash, primary CTA → getting-started); the checklist sub-FRs and concrete values (`#7cb3dd` dark link, `#1a1a1a` surface, verbatim fonts) confirmed as evidence-based refinements *within* the locked direction. Concrete values verified consistent across all artifacts **and against the real filesystem** (5 woff2 incl. `fira-code-regular.woff2`, 3 logo SVGs, 10 favicons all confirmed present; `first-run.md` route confirmed → links-validator will pass).

Two non-blocking findings, both **fixed by the orchestrator** (deterministic, no consensus):
- **C1 (MEDIUM, citation):** FR-016 had no explicit task citation → added to **T004** (the port-verification gate confirms the sourced/reconciled brand values landed).
- **C2 (LOW, prose):** plan's preload prose omitted the literal `crossorigin` → added (`each carrying crossorigin per FR-008; other 3 faces not preloaded`) for spec/plan parity.

**0 unresolved for consensus.**

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
| 1 - public/ assets (favicons, fonts) | T001–T004 | ✅ | 5 woff2 → `public/fonts/`, 10 favicons/manifest → `public/`, 3 logos → `src/assets/`; `robots.txt` untouched |
| 2 - brand.css tokens (light + dark) | T005–T007 | ✅ | `src/styles/brand.css` — token map, 5 `@font-face` (swap), font tokens, scoped hero/CTA/focus/reduced-motion |
| 3 - astro.config wiring (customCss, logo, favicon, fonts) | T011–T012 | ✅ | `customCss`/`logo`/`favicon`; appended 2 preloads (crossorigin) + favicon/theme to existing `head`; DOC-012 robots meta preserved |
| 4 - landing hero (index.mdx splash + CardGrid) | T008–T010 | ✅ | `template: splash` + hero (logomark, headline, value-prop, primary→`/first-run/`, secondary→GitHub) + 3 CardGrid cards |
| 5 - verify (validate, contrast, reduced-motion) | T013–T015 | ✅ | `validate` GREEN incl. 20/20 smoke; full contrast table all-AA; reduced-motion + soft-dark verified |

### Implementation Results (G7 ✅ — 2026-06-23)

`pnpm --dir docs-site validate` → **GREEN** (reference-check, astro check, links/build, safe-aids, quality, **20/20 Playwright smoke** — browser installed locally). Baseline confirmed pre-change. **23 files**: 19 new (5 woff2 + 10 favicon/manifest + 4 logo SVGs + `brand.css`) + 3 modified (`astro.config.mjs`, `index.mdx`, `tests/docs-smoke.spec.mjs`).

**WCAG-AA contrast — every pair PASSES** (measured): light link `#2a6a99`/`#f1f0ec` 5.09:1 · dark link `#7cb3dd`/`#1a1a1a` 7.75:1 · hero title `#fff`/`#0a0a0a` 19.8:1 · hero tagline `#ccc`/`#0a0a0a` 12.33:1 · white-on-red CTA `#fff`/`#dc143c` 4.99:1 · focus ring `#3c89c6` 3.30:1 light / 4.63:1 dark / 5.27:1 hero. **Red `#dc143c` appears ONLY in passing patterns** (white-on-red CTA, logo mark, `theme_color`) — never as small text, never `--sl-color-accent`. Soft-dark `#1a1a1a` reading surface; true-black `#0a0a0a` scoped to the splash hero only; reduced-motion guard present.

**Implement-time decisions / deviations (all justified):**
- **`mark-light.svg` created** (`mark.svg` shape `#111827`→`#ffffff`, red accent kept) — the dark logomark is illegible on the `#0a0a0a` hero; the brand source itself uses the white wordmark on its dark surface. Mirrors the `logo.svg`→`logo-light.svg` pattern. Hero uses the light mark in both modes; hero text is light; CTA is white-on-red.
- **`passthroughImageService()` added** to `astro.config.mjs` (one line) — Starlight's Hero renders `image` via Astro `<Image>`, which needs Sharp (only a transitive dep, unresolvable from docs-site root → `MissingSharp` build error). Passthrough serves the SVG vectors as-is (correct for logos; no rasterization) and adds no dependency.
- **Cross-spec contract update (DOC-010):** DOC-013's US1 intentionally makes the home `/` a marketplace splash whose `<h1>` is the hero headline. DOC-010 had hard-coded the home h1 as "Start". Resolution: kept the home **frontmatter `title: Start`** (preserves the DOC-010/DOC-002 IA label; the quality validator passes untouched), and updated **only** the smoke test's expected `/` h1 → the hero headline (with an explanatory comment). This is a sanctioned contract update reflecting the approved home-route change — not a test hack; the splash rewrite was not reverted.

### Self-Review (mandatory 4-question audit — 2026-06-23)

1. **Does it meet the spec?** Yes — all FRs/SCs implemented; full contrast table AA; red only in passing patterns; soft-dark surface; reduced-motion guard; preloads = exactly 2 with `crossorigin`.
2. **Any bug the validators would miss?** **YES — found + fixed.** `brand.css` initially listed the system font FIRST in every font stack (`system-ui, 'Geist', …`). Because `font-family` is a *preference* list (first AVAILABLE font wins) and the system font is always available, the brand faces (Geist / Space Grotesk / Fira Code) **would never render** — the site would ship+preload the fonts but show the system font. `validate` passes anyway (smoke checks heading *text*, not font-family). Fixed to brand-face-first (`'Geist', system-ui, …`), with `font-display: swap` preserving load-time visibility. Re-validated **green**.
3. **Did anything leak out of scope?** No — all changes inside `docs-site/`; `robots.txt` + DOC-012 meta preserved; no per-component restyle, perf budget, or tone system.
4. **Verified against the built DOM?** Yes — red hero CTA selector matches (`.hero .actions .sl-link-button.primary`); hero renders `mark-light.svg` + `alt`; brand fonts now lead the built CSS stacks; `mark-light.svg` differs from `mark.svg` only in the shape fill.

Self-review is a reporting step (never gates the PR) but here it caught a real defect before review.

---

## Post-Implementation Checklist

- [x] All tasks marked complete in tasks.md (T001–T016)
- [x] `pnpm --dir docs-site validate` passes (incl. 20/20 Playwright smoke)
- [x] `pnpm --dir docs-site build` succeeds (part of validate)
- [x] Light + dark mode WCAG AA verified (full contrast table, all pairs pass)
- [x] `bash tests/speckit-pro/run-all.sh` passes (3478/3478 after the privacy-scan fix)
- [x] **PR created:** [#246](https://github.com/racecraft-lab/racecraft-plugins-public/pull/246) — `feat(docs-site): apply Racecraft brand identity and marketplace landing page`

### Post-Implementation Summary (2026-06-24)

- **PR #246** opened on `doc-013-brand-identity-marketplace-landing` (11 commits → squash-merges as one).
- **Verification:** validate green (20/20 smoke); repo structural suite 3478/3478; full WCAG-AA contrast table all-pass; privacy scan 9/9.
- **Self-review caught + fixed** a real bug: brand fonts wouldn't render (system font led every stack); now brand-first.
- **Cross-spec contract update (DOC-010):** home `/` `<h1>` is now the hero headline; frontmatter `title: Start` kept as the IA label; only the smoke test's expected home heading updated (documented in PR body).
- **Reviewability override (operator-approved):** the final backstop blocked on `total_files 41 > 25`, inflated by 19 non-reviewable binary assets + SDD docs; `reviewable_loc` is 76, route is `one-navigable-PR`. Proceeded with a documented override (PR body §Scope). The backstop scratch (`gate-state.json`/`reslicing-packet.json`) was removed so it doesn't contradict the decision or pollute the spec map.
- **Two justified implement deviations:** derived `mark-light.svg` for dark-hero legibility; one-line `passthroughImageService()` to serve SVG logos without Sharp.
- **Privacy fix:** removed absolute local paths leaked from subagent prompts into `research.md`/`tasks.md`/`quickstart.md`.

### Follow-ups (separate from this PR)

- **PR #245** — `fix: honor feature.json branch bypass in SpecKit check-prerequisites` (the non-numeric-branch bug found at pre-flight; already open off `main`).
- **Reviewability-gate hardening (operator-approved follow-up):** exclude declared-non-reviewable binary assets from the `total_files` metric so asset-heavy specs don't false-trip the gate — its own plugin PR.
- **Review remediation `/loop`:** available but **not auto-scheduled** (a 3-day autonomous code-modifying cron — offered to the operator rather than started unprompted).

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
