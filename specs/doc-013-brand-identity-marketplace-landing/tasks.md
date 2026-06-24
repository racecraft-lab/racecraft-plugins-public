---
description: "Task list for DOC-013 — Brand identity and marketplace landing page"
---

# Tasks: Brand identity and marketplace landing page

**Input**: Design documents from `/specs/doc-013-brand-identity-marketplace-landing/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: This is a CSS/content/config slice with no application source and no
test harness. "Tests" here are the docs-site validators
(`pnpm --dir docs-site validate` = Astro check + `starlight-links-validator`
build + safe-aids + quality + Playwright smoke-preview) plus two explicit
manual-verification tasks the spec requires: a light+dark WCAG-AA contrast
table (SC-003) and a reduced-motion check (SC-008). These verification tasks
are made explicit, not implicit.

**Reviewability**: One thin vertical slice. Plan/spec estimator: ~80 reviewable
CSS LOC + a small MDX landing file + a handful of config lines (binary
font/favicon/logo assets are declared non-reviewable). Projected production
files: 2 (`brand.css`, `index.mdx`) + 1 config edit (`astro.config.mjs`);
6–8 total text/config files; **one** primary surface (UI). Within budget —
`suggested_slices: 1`, `status: ok`. **DO NOT split.** No reviewability
checkpoint task is required because the slice stays well under every warn
threshold (400 LOC / 6 production files / 15 total files / 1 primary surface),
but T009 records the no-split decision for the PR packet.

**Organization**: Tasks are grouped by user story. US1 = the branded landing
page (FR-001..004 + sub-FRs). US2 = consistent, accessible site-wide brand
identity (FR-005..017 + sub-FRs). Binary-asset ports and the brand stylesheet +
config wiring are shared prerequisites (Setup + Foundational) both stories
build on.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

All paths are under the existing `docs-site/` Astro/Starlight tree. Binary
brand assets are ported verbatim from the sibling brand-source project (the
`landing-page/website` checkout, a peer directory alongside this repository).
**`docs-site/public/robots.txt` MUST NOT be modified.** No files are created or
modified outside `docs-site/`.

---

## Phase 1: Setup (Shared Infrastructure — port binary brand assets)

**Purpose**: Bring the ported binary brand assets (fonts, favicons/manifest,
logo SVGs) into `docs-site/` so the stylesheet, config, and landing route can
reference them. These are non-reviewable artifacts under the budget. All three
porting tasks touch disjoint destination directories and are parallel-safe.

- [x] T001 [P] Port the 5 lean-set woff2 fonts verbatim from `landing-page/website/public/fonts/` into `docs-site/public/fonts/`: `space-grotesk-400.woff2`, `space-grotesk-700.woff2`, `geist-400.woff2`, `geist-600.woff2`, `fira-code-regular.woff2` (note the `-regular` filename, NOT `-400`, per research Decision 1 / VR-8). Ship ONLY these 5 — do NOT port `space-grotesk-300/500/600`, `geist-500/700/800`, or `fira-code-medium/semibold` (FR-007, VR-5). [research Decision 1]
- [x] T002 [P] Port the full favicon/icon set + webmanifest verbatim from `landing-page/website/public/` into `docs-site/public/` (10 files): `favicon.svg`, `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon-32x32-light.png`, `favicon-48x48.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `site.webmanifest` (verify `theme_color #dc143c` + `background_color #f1f0ec`). Place alongside the existing `public/robots.txt` WITHOUT modifying it (FR-011, VR-12, VR-13). [research Decision 2]
- [x] T003 [P] Port the 3 logo SVGs verbatim from `landing-page/website/src/assets/images/logos/` into `docs-site/src/assets/`: `logo.svg` (dark wordmark, viewBox `0 0 1956 287`, text `#111827` + mark `#dc143c`), `logo-light.svg` (light wordmark, text `#ffffff` + mark `#dc143c`), `mark.svg` (logomark, viewBox `0 0 1250 1041`, shape `#111827` + accent `#dc143c`). Create `docs-site/src/assets/` if absent (FR-009, FR-010, VR-9..VR-11). [research Decision 3]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Author the brand stylesheet token map + `@font-face` set and verify
the porting landed. `brand.css` is the backbone both user stories depend on
(US2 wires it site-wide; US1's hero CTA/true-black rules live in it). This phase
MUST complete before US1 or US2 work begins.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [x] T004 Verify all ported binary assets landed and `docs-site/public/robots.txt` is byte-unchanged: confirm the 5 woff2 in `docs-site/public/fonts/`, the 10 favicon/manifest files in `docs-site/public/`, and the 3 SVGs in `docs-site/src/assets/` all exist (depends on T001, T002, T003). This task confirms FR-016 is satisfied — brand values were sourced verbatim from the brand guide and reconciled against the authoritative live `landing-page/website` source (research Decisions 1–5 / data-model INV-2) before being applied. (VR-13, FR-016)
- [x] T005 Create `docs-site/src/styles/brand.css` with the light+dark `--sl-color-*` token map from research Decision 5 / data-model Entity 1: a `:root` block (dark default) and a `:root[data-theme='light']` block. Light: `--sl-color-accent #3c89c6`, `--sl-color-accent-low #d6e4f0`, `--sl-color-accent-high`/`--sl-color-text-accent #2a6a99`, `--sl-color-text #111827`, `--sl-color-bg #f1f0ec`, nav/sidebar `#f7f6f4`, border `#e8e7e3`, `--sl-color-white #111827`. Dark: `--sl-color-accent #3c89c6`, `--sl-color-accent-low #13283a`, `--sl-color-accent-high`/`--sl-color-text-accent #7cb3dd`, `--sl-color-text #e6e6e6`, `--sl-color-bg #1a1a1a`, nav/sidebar `#1f2937`, border `rgba(255,255,255,0.10)`, `--sl-color-white #ffffff`. Red `#dc143c` MUST NOT be wired into `--sl-color-accent` (FR-005/005a/006/012/013/014, VR-1..VR-4). [research Decision 5] (depends on T004)
- [x] T006 In `docs-site/src/styles/brand.css` add the five `@font-face` blocks (one per ported woff2), each with `font-display: swap` and `src: url('/racecraft-plugins-public/fonts/<file>.woff2')` — `space-grotesk-400.woff2` (Space Grotesk 400), `space-grotesk-700.woff2` (Space Grotesk 700), `geist-400.woff2` (Geist 400), `geist-600.woff2` (Geist 600), `fira-code-regular.woff2` (Fira Code 400). Then assign Starlight font tokens with a system fallback FIRST in each stack: `--sl-font: "Geist", system-ui, sans-serif`, `--sl-font-mono: "Fira Code", ui-monospace, monospace`, and heading/display selectors → `"Space Grotesk", system-ui, sans-serif` (FR-007/008, VR-5..VR-8; SC-005). [research Decision 5 / data-model Entity 2] (depends on T005)
- [x] T007 In `docs-site/src/styles/brand.css` add the scoped non-token rules: (a) the true-black hero block `#0a0a0a` scoped to the splash hero ONLY (`.hero`/splash selector) — true black MUST NOT touch the `#1a1a1a` reading surface (FR-013, SC-004, VR-3); (b) the hero primary-CTA rendered as white text on a red fill (`#ffffff` on `#dc143c` = 4.99:1, AA-pass) — red as small foreground text on `#f1f0ec` (4.38:1) or `#0a0a0a` (3.97:1) is FORBIDDEN (FR-005a); (c) a visible keyboard focus-ring using non-text blue `#3c89c6` meeting ≥3:1 in both modes (3.30:1 on `#f1f0ec`, 4.63:1 on `#1a1a1a`) on links/nav/CTAs (FR-014a); (d) a `@media (prefers-reduced-motion: reduce)` guard suppressing/reducing entrance animation (FR-015, SC-008, VR-19). [plan File-by-file #1] (depends on T005, T006)

**Checkpoint**: Assets ported + verified, `brand.css` complete (tokens + fonts +
scoped red/hero/focus/reduced-motion). US1 and US2 can now proceed.

---

## Phase 3: User Story 1 - Branded marketplace landing page (Priority: P1) 🎯 MVP

**Goal**: Turn the stock-Starlight home route into a Starlight-native splash
landing page: logomark hero image + benefit-led headline + plain-English
value-prop + exactly one primary CTA (→ first-run tutorial) + one subordinate
secondary CTA (→ GitHub) + ~3 anti-hype value-prop cards.

**Independent Test**: Load the docs home route and confirm it renders as a
splash landing (mark + headline + value-prop + primary CTA + secondary CTA),
NOT a generic doc article with a sidebar body; the primary CTA links to the
getting-started/first-workflow tutorial and the secondary to the GitHub repo;
~3 plain-English cards summarize the offering; the {mark, headline, value-prop,
primary CTA} set is comprehensible within the first screen on both desktop and
mobile widths.

### Implementation for User Story 1

- [x] T008 [US1] Rewrite `docs-site/src/content/docs/index.mdx` to a Starlight-native landing page (no bespoke components, VR-18): frontmatter `template: splash` + `hero` with a benefit-led `title` (states a reader-facing outcome of spec-driven development, NOT a product/feature name — FR-002), a plain-English `tagline` value-prop (distinct from a feature list — FR-002), `image: { light: ../../assets/mark.svg, dark: ../../assets/mark.svg }` (FR-010, VR-11), and `hero.actions` = EXACTLY ONE primary `{ variant: 'primary', link: '/racecraft-plugins-public/first-run/' }` plus ONE subordinate secondary `{ variant: 'minimal' (or 'secondary'), link: 'https://github.com/racecraft-lab/racecraft-plugins-public' }` — NO third/competing action; primary MUST carry dominant/filled weight, secondary lower-emphasis (FR-001, FR-002, FR-003, FR-003a, SC-006, VR-14, VR-15). The above-the-fold set {mark, headline, value-prop, primary CTA} MUST fit the first screen on desktop AND mobile (FR-001a, SC-001, VR-17). [plan File-by-file #3] (depends on T003 mark.svg, T007 hero CTA rule)
- [x] T009 [US1] In `docs-site/src/content/docs/index.mdx` body, import `CardGrid` + `Card` from `@astrojs/starlight/components` and render the value-prop cards: 3 by default (2–4 allowed), each a scannable benefit-led title + brief plain-English blurb expressing a user-facing benefit, NOT an internal feature label/jargon (FR-004, VR-16, AS Story-1 #3). (depends on T008)
- [x] T010 [US1] Verify all landing copy authored in T008–T009 (headline, tagline, every card title/blurb) satisfies the anti-hype testable rule (FR-004a): (a) NO marketing-hype/unsubstantiated superlatives ("revolutionary", "game-changing", "the best", "effortless", "magical", "supercharge", "10x", "world-class", "AI-powered" as a boast); (b) NO unexplained internal jargon/acronyms a first-time visitor would not know; (c) value stated as a concrete, verifiable capability/outcome. Record this as a copy-review note for the PR packet. (depends on T008, T009)

**Checkpoint**: The home route renders as a branded splash landing, build-verified
(primary CTA slug `/racecraft-plugins-public/first-run/` is checked by
`starlight-links-validator`). US1 is independently demonstrable.

---

## Phase 4: User Story 2 - Consistent, accessible site-wide brand identity (Priority: P2)

**Goal**: Generalize the brand from the landing page to every route, in both
light and dark mode: wire `brand.css` site-wide, set the header wordmark
(light/dark variants), the favicon set + browser theme color, and the two
critical font preloads — all while keeping WCAG AA contrast and a visible focus
indicator.

**Independent Test**: Navigate several interior docs routes in both light and
dark mode and confirm the brand accent on links/active-nav, brand typefaces in
headings/body/code, the correct light/dark wordmark in the header, the brand
favicon in the browser tab, a soft-dark `#1a1a1a` reading surface (true black
only on the hero), a visible focus ring on keyboard focus, and no unstyled
fallback — with text/interactive contrast meeting WCAG AA in both modes.

### Implementation for User Story 2

- [x] T011 [US2] In `docs-site/astro.config.mjs`, inside the existing `starlight({…})` call, add the net-new keys: `customCss: ['./src/styles/brand.css']`, `logo: { light: './src/assets/logo.svg', dark: './src/assets/logo-light.svg', replacesTitle: true, alt: 'Racecraft' }`, and `favicon: '/favicon.svg'`. Leave the existing `title`, `plugins`, and `sidebar` intact. `replacesTitle: true` keeps `title` as the accessible site name and the header logo as the home link (FR-009, FR-012, VR-9, VR-10; INV-1). [research Decision 4 / plan File-by-file #2] (depends on T003, T005)
- [x] T012 [US2] In `docs-site/astro.config.mjs`, APPEND to the EXISTING `head` array (do NOT replace the existing `<meta name="robots" content="noindex, nofollow">` DOC-012 staging guard): the TWO font preload tags ONLY — `<link rel="preload" href="/racecraft-plugins-public/fonts/space-grotesk-700.woff2" as="font" type="font/woff2" crossorigin>` and the same for `geist-400.woff2` — each carrying `crossorigin` (FR-008, VR-7). The other 3 faces (Space Grotesk 400, Geist 600, Fira Code 400) MUST NOT be preloaded. Also append the favicon/apple-touch-icon/manifest `<link>` tags and the `theme-color` `<meta>` (base-path-prefixed hrefs) so the brand favicon + theme color apply (FR-011, VR-12). [research Decision 4 / plan File-by-file #2] (depends on T002, T011)

**Checkpoint**: Brand identity (tokens + fonts + wordmark + favicon + theme
color + focus ring) applies across all routes in both modes. US2 is
independently testable on interior routes.

---

## Phase 5: Polish & Verification (Cross-Cutting)

**Purpose**: Run the docs-site validators and the two explicit accessibility
verifications the spec mandates, then assemble the PR review packet. These gate
SC-002, SC-003, SC-004, SC-005, SC-006, SC-008.

- [x] T013 Run `pnpm --dir docs-site validate` (Astro check + `starlight-links-validator` build + safe-aids + quality + Playwright smoke-preview) and confirm it passes — this build-verifies the primary CTA slug `/racecraft-plugins-public/first-run/` and the secondary GitHub link have no broken links (SC-006, SC-008, VR-15). (depends on T012, T010)
- [x] T014 Produce the explicit WCAG-AA contrast verification: an enumerated table of foreground-background pairs each with its measured ratio + threshold, in BOTH light and dark mode, covering — link text (`#2a6a99` on `#f1f0ec` ≈ 5.09:1; `#7cb3dd` on `#1a1a1a` ≈ 7.75:1), body text (`#111827` on `#f1f0ec`; `#e6e6e6` on `#1a1a1a`), the non-text blue accent (`#3c89c6`, 3:1 non-text), the keyboard focus ring (`#3c89c6` 3.30:1 on `#f1f0ec`, 4.63:1 on `#1a1a1a`), and red punctuation — confirming red appears ONLY in a passing pattern (white-on-red CTA fill `#ffffff` on `#dc143c` = 4.99:1, large/non-text accent, or logo-mark logotype) and NEVER as failing normal-size red text (FR-005a/006/014/014a, SC-003, VR-1/VR-2). Record as PR evidence. (depends on T013)
- [x] T015 Verify reduced-motion + dark-surface invariants in a preview: confirm any entrance animation is suppressed/reduced under `prefers-reduced-motion: reduce` (FR-015, SC-008, VR-19); confirm the dark-mode reading surface is `#1a1a1a` on interior routes and true black `#0a0a0a` appears ONLY on the decorative hero block (FR-013, SC-004); spot-check the hero `hero.image` carries the `alt` value and the header shows the correct light/dark wordmark with no flash of the wrong theme (FR-010, AS Story-2 #3, VR-10). (depends on T013)
- [ ] T016 Assemble the PR review packet per the spec's PR Review Packet Requirements: what changed, why, non-goals (name the deferred specs DOC-016 / DOC-017 / DOC-019 / DOC-012), review order (`brand.css` → `astro.config.mjs` → `index.mdx` → spot-check ported assets), scope budget, traceability (FR-005/005a/006 → `brand.css` + contrast table; FR-001–004 → `index.mdx`; FR-007/008 → `@font-face` + preloads; FR-009/010/011 → config + assets; FR-013 → scoped hero/soft-dark; FR-014a → focus ring), verification evidence (the T013 build + the T014 contrast table), known gaps, and rollback notes (clean delete of `brand.css` + ported assets, restore `astro.config.mjs`/`index.mdx`). Confirm no scope leaked into DOC-016/017/019/012 (FR-017, SC-007, INV-3). (depends on T014, T015)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001/T002/T003 port to disjoint directories, all `[P]`.
- **Foundational (Phase 2)**: Depends on Setup. T004 verifies the ports; T005→T006→T007 author `brand.css` in sequence (same file). BLOCKS both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational (needs `mark.svg` from T003 and the hero-CTA rule from T007). T008→T009→T010 are sequential (same `index.mdx`, then a copy review).
- **User Story 2 (Phase 4)**: Depends on Foundational (needs the logo SVGs, `brand.css`, and the ported favicons/fonts). T011→T012 are sequential (same `astro.config.mjs`).
- **Polish (Phase 5)**: Depends on US1 + US2 complete. T013 (validate) → T014/T015 (a11y verifications) → T016 (PR packet).

### User Story Dependencies

- **US1 (P1)**: Can start once Foundational is done. Touches `index.mdx` only; independently testable.
- **US2 (P2)**: Can start once Foundational is done. Touches `astro.config.mjs` only; independently testable. US1 and US2 edit different files, so once Foundational completes they can proceed in parallel.

### Within Each Phase / Story

- Setup: T001/T002/T003 parallel.
- Foundational: T004 first; then T005 → T006 → T007 (all the same `brand.css`, so sequential).
- US1: T008 → T009 → T010 (same `index.mdx`, then copy review).
- US2: T011 → T012 (same `astro.config.mjs`).
- Polish: T013 → {T014, T015} → T016.

### Parallel Opportunities

- All three Setup ports (T001 fonts, T002 favicons, T003 logos) run in parallel — disjoint destinations.
- After Foundational (T004–T007) completes, US1 (`index.mdx`) and US2 (`astro.config.mjs`) can be worked in parallel — different files, no cross-story dependency.
- Within Polish, T014 (contrast table) and T015 (reduced-motion/dark-surface check) are independent observations on the same preview and may run in parallel after T013.

---

## Parallel Example: Setup (Phase 1)

```bash
# Port all three binary-asset groups together (disjoint destinations):
Task: "T001 Port 5 woff2 fonts → docs-site/public/fonts/"
Task: "T002 Port favicon set + webmanifest → docs-site/public/ (not robots.txt)"
Task: "T003 Port 3 logo SVGs → docs-site/src/assets/"
```

## Parallel Example: After Foundational

```bash
# US1 and US2 touch different files — run in parallel:
Task: "T008 Rewrite index.mdx to splash + hero (US1)"
Task: "T011 Add customCss/logo/favicon to astro.config.mjs (US2)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1: Setup (port assets).
2. Complete Phase 2: Foundational (`brand.css` — blocks both stories).
3. Complete Phase 3: User Story 1 (splash landing).
4. **STOP and VALIDATE**: confirm the home route renders as a branded splash with the four above-the-fold elements and the two CTAs.
5. Demo if ready — the landing page is the highest-stakes newcomer surface and stands alone.

### Incremental Delivery

1. Setup + Foundational → assets + stylesheet ready.
2. Add US1 → splash landing demonstrable (MVP).
3. Add US2 → brand applies site-wide in both modes.
4. Polish → validators + contrast table + reduced-motion check + PR packet.

Because US1 and US2 edit different files, in a single-developer flow the natural
order is Foundational → US2 (wire `brand.css`/logo/favicon site-wide so interior
routes are branded) → US1 (author the landing content) → Polish; or US1 → US2 if
the landing page is demoed first. Either order works since the two stories are
file-disjoint.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] label maps each landing/site-wide task to its user story for traceability; Setup/Foundational/Polish carry no story label.
- Binary font/favicon/logo assets are non-reviewable artifacts under the budget — they are ported verbatim, not authored.
- `docs-site/public/robots.txt` MUST NOT be modified (VR-13); the DOC-012 robots `<meta>` in `astro.config.mjs` head MUST be preserved (append, never replace).
- Bound by Non-goals: no per-component restyle (DOC-016), no perf/Lighthouse budget (DOC-017), no verbal-voice/tone system (DOC-019), no domain/base-path cutover (DOC-012). Landing copy direction (anti-hype, plain-English) is in scope; a full tone system is not.
- Single vertical slice — DO NOT split. The plan/spec estimator reports `suggested_slices: 1`, within budget.
- Commit after each task or logical group.
