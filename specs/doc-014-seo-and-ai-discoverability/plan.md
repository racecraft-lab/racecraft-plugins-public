# Implementation Plan: SEO and AI Discoverability

**Branch**: `doc-014-seo-and-ai-discoverability` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/doc-014-seo-and-ai-discoverability/spec.md`

## Summary

Make the Astro/Starlight docs site discoverable by classic search and AI
answer/coding engines before public launch, while it remains on its noindex'd
staging URL. The feature adds, all derived from the single `site`+`base` config
(so it finalizes automatically at the DOC-012 launch flip):

- a 3-tier crawler-access policy (`robots.txt.ts` endpoint) that **allows** the
  AI-training tier (inverting the sibling) plus the citation tier and default;
- agent-readable content: `starlight-llms-txt` digests + a dependency-free
  per-page raw-Markdown endpoint;
- a JSON-LD `@graph` (Organization + WebSite site-wide, SoftwareApplication on
  the landing page, Person) injected via a Starlight **route-data middleware**;
- per-page dynamic Open Graph cards (`astro-og-canvas` + an `OGImageRoute`),
  tagged per page by the same middleware;
- a git-accurate sitemap `<lastmod>` (`@astrojs/sitemap` promoted to a direct dep
  with a custom `serialize()`) + Starlight's visible `lastUpdated` stamp;
- meta `description` on all 19 content pages (12 authored + 7 emitted by the
  reference generator) with a presence-requiring quality-gate rule;
- a documented "AI-discoverable" success metric (definition + measurement source,
  no numeric target).

The technical approach and every open decision are resolved in
[research.md](./research.md); shapes are in [data-model.md](./data-model.md);
the consumer-facing surfaces are in
[contracts/build-output-contracts.md](./contracts/build-output-contracts.md).

## Technical Context

**Language/Version**: Docs-site JavaScript/TypeScript ESM on Node `>=22.12`;
GitHub Actions YAML; Markdown/MDX content + frontmatter.

**Primary Dependencies**: Astro 6.4.6, `@astrojs/starlight` 0.40.0 (static
output), `pnpm@10.25.0` (Corepack). Existing: `starlight-links-validator` 0.24.1,
`passthroughImageService` (DOC-013), `@playwright/test` 1.61.0 (Chromium),
`validate-docs-quality.mjs` (JS ESM gate). **New direct deps**:
`starlight-llms-txt` 0.10.0, `astro-og-canvas` 0.11.1 (+ `canvaskit-wasm`),
`@astrojs/sitemap` 3.7.3 (promoted from transitive).

**Storage**: N/A — checked-in repository files only; all outputs are produced at
`astro build` time. GitHub Pages stores the uploaded `docs-site/dist` artifact
outside source control.

**Testing**: `pnpm --dir docs-site validate` (reference check, `astro check`,
build/links, safe-aids, quality gate, Playwright smoke). New Playwright specs
(Chromium-only) under `docs-site/tests/`.

**Target Platform**: Static site served from GitHub Pages at
`https://racecraft-lab.github.io/racecraft-plugins-public/` (staging; DOC-012
owns the launch flip to the production domain).

**Project Type**: Static documentation site (Astro/Starlight) within a plugin
marketplace monorepo. All work is scoped to `docs-site/` plus one CI workflow
line and one success-metric doc.

**Performance Goals**: No *runtime* perf target — every new surface is produced
at `astro build` with `prerender = true` and served as a static artifact, so it
adds zero request-time/served cost (DOC-017 owns the runtime Lighthouse budget).
The relevant cost dimension here is **build time + build-output size**, and the
expectation is that both stay within reasonable bounds for the current ~19 content
pages and scale linearly as that set grows. Cost breakdown:
- **OG cards (`astro-og-canvas` / canvaskit-wasm)**: a one-time CanvasKit/Skia WASM
  load plus one small PNG render per content page (~19 renders), all at build time
  via `OGImageRoute` `getStaticPaths`. This is the proven Starlight OG path; no
  caching layer is warranted at this scale (KISS). Output = ~19 small PNGs in
  `dist`. The cards are referenced only in `<head>` (`og:image`/`twitter:image`)
  and are **not** render-blocking or on-page-loaded assets (contracts C6).
- **Per-page `.md` (`[...slug].md.ts`)**: a raw-`body` passthrough per page (no
  rendering), trivially cheap; output is bounded text proportional to content. It
  is a separate fetchable route, not an asset the rendered HTML loads (contracts C4).
- **llms.txt digests (`starlight-llms-txt`)**: three build-time text passes over
  the content model; bounded text output, separate routes (contracts C5).
- **Sitemap `<lastmod>` git lookups**: see the batched-lookup constraint below —
  the dates MUST be collected with a single bulk `git log` walk, not one
  subprocess per page.
- **Build-failure posture (all generated surfaces, never silent)**: OG cards, the
  per-page `.md` endpoint, the `starlight-llms-txt` digests, the sitemap, and the
  JSON-LD graph are all produced inside `astro build`, so a generation error on ANY
  of them fails the build loudly rather than silently shipping a missing/broken/empty
  artifact for a page. "Loud" is verifiable because that `astro build` is the step
  inside `pnpm --dir docs-site validate` that the `validate-docs` CI job runs — a
  failed generation is a non-zero build, not a degraded output (spec Edge Cases
  "Generation failure for a single page must not ship silently"; consistent with the
  deterministic `validate` gate). The `robots.txt` endpoint and per-page `.md` are
  `prerender = true`, so they are produced at build time and served as static files
  with no request-time/runtime failure path — "always emits a valid response" is a
  structural property of static generation, not runtime error handling (FR-001).

**Constraints**: Keep `site: 'https://racecraft-lab.github.io'` +
`base: '/racecraft-plugins-public'` (no hardcoded production domain — FR-012);
keep the DOC-011 `noindex, nofollow` head guard intact (FR-029); single canonical
source — do NOT add `astro-seo` (FR-027); no `FAQPage`/`HowTo` and no
`Accept`-header content negotiation (FR-028); KISS/YAGNI (constitution VI). The
sitemap `serialize()` MUST collect per-page git dates with a **single bulk
`git log` walk**, not one `git log` subprocess per page — per-file invocation is
a known O(pages) build-cost problem (withastro/astro#16803), and Starlight's own
`lastUpdated` already uses a bulk walk; the feature MUST NOT add new
render-blocking or on-page-loaded assets (build outputs are off-page routes/PNGs
referenced only in `<head>`), so DOC-017 inherits a clean perf baseline.

**Scale/Scope**: 19 content pages (12 hand-authored + 7 generated reference).
~300–360 reviewable production LOC (human estimate), one spec, no split.

**Reviewability Budget**: Primary surface = docs/process (`docs-site/`
configuration, metadata, content frontmatter). Secondary = seed/config
(crawler-access policy + structured-data/social-card/sitemap wiring). Projected
reviewable LOC ~300–360 (human), under the 400 warn / 800 block LOC ceiling.
Production files: see the file-count tension recorded in **Constitution Check**.
Budget result: within the LOC ceiling; one spec with a documented A/B fallback.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc.sh`) parses this
block. Generated/binary build inputs (the OG display face + PNG logo, generated
card images, generated digests, generated per-page `.md`) are excluded per the
spec's Reviewability Notes and are NOT listed here. Lockfile churn is a generated
artifact (the estimator excludes it from the production count).

- NEW docs-site/src/pages/robots.txt.ts
- NEW docs-site/src/pages/[...slug].md.ts
- NEW docs-site/src/pages/og/[...slug].ts
- NEW docs-site/src/routeData.ts
- NEW docs-site/src/lib/schema.ts
- NEW docs-site/tests/seo-robots-txt.spec.mjs
- NEW docs-site/tests/seo-schema-org.spec.mjs
- NEW docs-site/tests/seo-llms-txt.spec.mjs
- NEW docs-site/tests/seo-sitemap.spec.mjs
- NEW docs/ai/specs/doc-014-ai-discoverability-success-metric.md
- MODIFIED docs-site/astro.config.mjs
- MODIFIED docs-site/package.json
- MODIFIED docs-site/pnpm-lock.yaml
- MODIFIED docs-site/playwright.config.mjs
- MODIFIED docs-site/scripts/validate-docs-quality.mjs
- MODIFIED docs-site/scripts/generate-reference-pages.mjs
- MODIFIED docs-site/src/content/docs/index.mdx
- MODIFIED docs-site/src/content/docs/choose-your-path.mdx
- MODIFIED docs-site/src/content/docs/spec-kit-lifecycle.mdx
- MODIFIED docs-site/src/content/docs/first-run.md
- MODIFIED docs-site/src/content/docs/glossary.md
- MODIFIED docs-site/src/content/docs/reference.md
- MODIFIED docs-site/src/content/docs/security-and-trust.md
- MODIFIED docs-site/src/content/docs/troubleshooting.md
- MODIFIED docs-site/src/content/docs/update-and-rollback.md
- MODIFIED docs-site/src/content/docs/contribute-and-release.md
- MODIFIED docs-site/src/content/docs/install/claude-code.md
- MODIFIED docs-site/src/content/docs/install/codex.md
- MODIFIED .github/workflows/deploy-docs.yml

Per-file LOC intent (human estimate, for the reviewer — production source only):
`robots.txt.ts` ~45, `[...slug].md.ts` ~15, `og/[...slug].ts` ~25,
`routeData.ts` ~50, `lib/schema.ts` ~60, `astro.config.mjs` +~40,
`validate-docs-quality.mjs` +~35, `generate-reference-pages.mjs` +~15,
`playwright.config.mjs` +~1, 12 content frontmatter lines ~12, `package.json`
+~4, success-metric doc ~50, 4 test specs ~40 each (~160). Production prose
(excluding the 4 test specs) ≈ **300–360 reviewable LOC**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution v1.1.0 — relevant principles:

- **I. Plugin Structure / III. Semantic Versioning** — N/A. This feature touches
  no plugin manifest, no `marketplace.json`, no release config; it is docs-site +
  one CI line. No version bump (docs-site `package.json` `version` stays `0.0.0`).
- **II. Script Safety** — N/A for shell (no bash scripts added). The two modified
  `.mjs` scripts follow the existing ESM diagnostics-array style.
- **IV. Test Coverage Before Merge** — Satisfied via the docs-site gate, not the
  plugin Layer suite. The docs-site has its own `pnpm --dir docs-site validate`
  contract (the analogue of `tests/run-all.sh` for this surface). New behavior is
  covered by 4 Playwright specs + the new `validateMetaDescriptions` quality rule.
  The plugin's `tests/run-all.sh` is unaffected (no plugin files change), and the
  `validate-docs` CI job runs the docs validation for docs-site changes.
- **V. Conventional Commits** — Satisfied. PR title will be
  `feat(docs): …` / `docs: …`-shaped, plain-English per the repo's public-readable
  rule. (Orchestrator owns commits.)
- **VI. KISS, Simplicity & YAGNI** — Satisfied by design: per-page `.md` is a
  ~15-line endpoint (no plugin); JSON-LD uses route middleware (Starlight's
  recommended path, not a `Head.astro` last resort); canonical relies solely on
  the built-in (no `astro-seo`); `schema-dts` typing dep is **not** added; no
  `FAQPage`/`HowTo`; `site` is not parameterized for environments (DOC-012 owns
  the one-line flip). Each new dependency maps to exactly one required surface
  (digests, OG cards, git-dated sitemap).

### Reviewability budget gate (constitution + plan-template thresholds)

Thresholds: **warn** above 400 reviewable LOC / 6 production files / 15 total
files / >1 primary surface; **block** above 800 reviewable LOC / 8 production
files / 25 total files / >1 primary surface unless a ratified split exception
exists.

| Dimension | Value | Warn (>) | Block (>) | Result |
|-----------|-------|----------|-----------|--------|
| Reviewable LOC (human, production prose) | ~300–360 | 400 | 800 | **under warn** |
| Reviewable LOC (mechanical `estimate-reviewable-loc.sh` = production-files × 40) | ~520 | 400 | 800 | over warn, **under block** → estimator `status: pass` |
| Production files (estimator's classification, incl. 4 `.mjs` test specs) | 13 | 6 | 8 | **over block on file count** |
| Production files (behavior-changing source, excluding the 4 tests + the 12 one-line content edits) | 7 | 6 | 8 | over warn, under block |
| Total files (incl. spec/plan/tasks + content edits) | ~33 | 15 | 25 | **over block on total count** |
| Primary surfaces | 1 (docs/process) | 1 | 1 | **at limit (OK)** |

**Recorded tension (surfaced, not silently passed)**: the mechanical
file-/total-count thresholds trip the *block* line (13 production files, ~33 total
files), while the **reviewable-LOC** ceiling — the dimension the constitution
frames as primary and the one the spec budgeted — stays comfortably under warn
(~300–360 < 400). Three things explain the count overshoot, none of which is a
true atomicity problem:

1. The estimator's `files × 40` heuristic over-projects when most files are tiny
   (a 1-line content-frontmatter edit and a 15-line endpoint both count as
   "40 LOC"). This is the known estimator behavior; the production-LOC ceiling is
   the authoritative reviewability dimension.
2. 4 of the 13 "production" files are **Playwright test specs** (`.mjs`), which the
   estimator classifies as production but which are test coverage, not shipped
   behavior. Excluding them, behavior-changing source is **7 files**.
3. 12 of the file entries are **one-line `description:` additions** to existing
   content pages — mechanically "modified files," substantively a single authored
   sentence each.

**Split decision (ratified by the resolved Clarify decisions): remains ONE
spec.** The reviewable surface is tightly coupled SEO work on the same
`astro.config.mjs` + page-head + sitemap surface; splitting would create two PRs
that both edit `astro.config.mjs` and the shared route-data middleware — an
artificial seam. The documented fallback (if the post-Tasks `atomicity-route.sh`
classifier recommends a split-PR emission at change-emission time) is the A/B
seam already recorded in the spec: **A** = crawler/agent access (robots.txt +
llms.txt + per-page `.md`); **B** = metadata/structured-data/cards/sitemap/metric.
That is a downstream PR-emission decision, not a spec split. This plan records the
exception rationale here so the gate verdict is explicit rather than implicit.

### PR review packet source (per spec "PR Review Packet Requirements")

- **What changed / why**: the Summary above + per-surface contracts.
- **Non-goals**: FR-024…FR-029 boundaries (no training block; no prose rewrite;
  no analytics/404/legal/domain-flip; no second canonical; no FAQ/HowTo or
  content negotiation; noindex guard preserved).
- **Review order**: (1) `robots.txt.ts` + `public/robots.txt` removal +
  quality-gate retarget; (2) `routeData.ts` + `lib/schema.ts` (structured data +
  OG tags); (3) `[...slug].md.ts` + `astro.config.mjs` plugins/integrations
  (digests, sitemap, lastUpdated); (4) OG route + assets; (5) descriptions +
  generator emission + `validateMetaDescriptions`; (6) success-metric doc +
  `deploy-docs.yml` fetch-depth.
- **Scope budget**: this section.
- **Traceability**: each FR group → files → verification, in `contracts/` (C1–C11)
  and `data-model.md`.
- **Verification**: `pnpm --dir docs-site validate` green + the new SEO specs;
  `quickstart.md` per-surface checks.
- **Known gaps / deferred**: meta-description refresh → DOC-015; analytics
  activation + launch hygiene → DOC-018; production-domain flip + noindex removal
  → DOC-012; numeric success-metric target → post-launch baseline.
- **Rollback/flags**: additive; the staging noindex guard stays, so rollback is
  removal of the added policy/metadata without affecting indexing posture.

### CI note (CLAUDE.md convention)

This feature edits `.github/workflows/deploy-docs.yml` (the `actions/checkout`
step gains `fetch-depth: 0`). Per CLAUDE.md, the PR description must confirm
CLAUDE.md's CI/CD sections need no update — this is a checkout-depth change, not a
job rename, permission change, or required-check-name change, so branch-protection
drift detection does not apply.

## Project Structure

### Documentation (this feature)

```text
specs/doc-014-seo-and-ai-discoverability/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — all decisions resolved (D1–D12)
├── data-model.md        # Phase 1 — build-time data shapes (6 entities)
├── quickstart.md        # Phase 1 — validation runbook
├── contracts/
│   └── build-output-contracts.md   # Phase 1 — C1–C11 consumer-facing contracts
└── tasks.md             # Phase 2 — created by /speckit-tasks (NOT here)
```

### Source Code (repository root)

```text
docs-site/
├── astro.config.mjs                       # MODIFIED: integrations (sitemap+serialize), plugins
│                                          #   (starlight-llms-txt), routeMiddleware, lastUpdated
├── package.json                           # MODIFIED: + starlight-llms-txt, astro-og-canvas,
│                                          #   canvaskit-wasm, @astrojs/sitemap
├── pnpm-lock.yaml                         # MODIFIED (generated): regenerated by pnpm install
├── playwright.config.mjs                  # MODIFIED: broaden testMatch to a glob
├── scripts/
│   ├── validate-docs-quality.mjs          # MODIFIED: + validateMetaDescriptions; retarget the
│   │                                      #   robots assertion; KEEP the noindex-meta assertion
│   └── generate-reference-pages.mjs       # MODIFIED: emit description: in renderPage frontmatter
├── src/
│   ├── routeData.ts                       # NEW: route-data middleware (JSON-LD + OG/twitter tags)
│   ├── lib/
│   │   └── schema.ts                       # NEW: ported schema factory funcs + pluginPages map
│   ├── pages/
│   │   ├── robots.txt.ts                   # NEW: 3-tier crawler policy + Sitemap from site+base
│   │   ├── [...slug].md.ts                 # NEW: per-page raw-body Markdown endpoint
│   │   └── og/
│   │       └── [...slug].ts                # NEW: OGImageRoute per-page card endpoint
│   ├── assets/
│   │   └── og/                             # build inputs (excluded LOC): .ttf/.otf face + PNG logo
│   └── content/docs/                       # MODIFIED: + description: on the 12 hand-authored pages
│       ├── index.mdx  choose-your-path.mdx  spec-kit-lifecycle.mdx
│       ├── first-run.md  glossary.md  reference.md  security-and-trust.md
│       ├── troubleshooting.md  update-and-rollback.md  contribute-and-release.md
│       └── install/{claude-code.md, codex.md}
│       # (reference/*.md — the 7 generated pages — get their description from the generator)
├── public/
│   └── robots.txt                          # DELETED: would shadow the robots.txt.ts endpoint
└── tests/
    ├── docs-smoke.spec.mjs                  # existing (unchanged)
    ├── seo-robots-txt.spec.mjs              # NEW: training ALLOWED (inverse of sibling)
    ├── seo-schema-org.spec.mjs              # NEW: Org @id == WebSite publisher @id; SWApp price 0
    ├── seo-llms-txt.spec.mjs                # NEW: 3 digests 200 + non-empty
    └── seo-sitemap.spec.mjs                 # NEW: <lastmod> valid ISO from git, not build time

docs/ai/specs/
└── doc-014-ai-discoverability-success-metric.md   # NEW: definition + measurement source, no target

.github/workflows/
└── deploy-docs.yml                          # MODIFIED: actions/checkout fetch-depth: 0
```

**Structure Decision**: Single static-site surface (`docs-site/`) plus one CI
workflow line and one success-metric doc. No new top-level project; no plugin
changes. New endpoints live under `docs-site/src/pages/` (Astro file-based
routing); shared logic in `docs-site/src/lib/` and `docs-site/src/routeData.ts`;
tests alongside the existing smoke spec in `docs-site/tests/`. This matches the
DOC-004/007/008/010/011 docs-site conventions already recorded in CLAUDE.md.

## Implementation notes (carried to Tasks/Implement)

- **`node_modules` is absent** in this worktree's `docs-site/`. Implement MUST run
  `pnpm --dir docs-site install` after editing `package.json`, then
  `pnpm --dir docs-site exec playwright install --with-deps chromium`. The
  regenerated `pnpm-lock.yaml` MUST be committed (CI uses `--frozen-lockfile`).
- **`playwright.config.mjs` `testMatch` is single-file** (`'docs-smoke.spec.mjs'`);
  broaden to a glob (e.g. `'**/*.spec.mjs'`) or the new SEO specs never run.
- **`generate-reference-pages.mjs`**: `renderPage()` currently emits `description`
  as body text; add a `description:` line to its frontmatter block (lines ~671–675)
  — `reference:check` (`--check`) must still pass after the change.
- **`validate-docs-quality.mjs`**: the robots retarget is in
  `validateStagingIndexingGuard()` (the `DOC011_STAGING_ROBOTS_*` constants at
  ~line 69 and the assertion at ~lines 423–430); **keep** the noindex-meta
  assertion (~lines 432–438). `validateMetaDescriptions` is a new function added to
  the `validateDocsQuality()` runner (~line 506).
- **OG assets** (`.ttf`/`.otf` + PNG): CanvasKit rejects `woff2`/`SVG`. These are
  build inputs under `docs-site/src/assets/og/`, excluded from reviewable LOC.
- **Sitemap git dates — batch, do NOT call `git log` per page.** The custom
  `serialize()` MUST resolve every page's commit date from a **single** bulk
  `git log` walk built once before serialize runs (e.g. one
  `git log --name-only --pretty=%cI` pass, or `git log -1 --format=%cI -- <all
  files>` collected into a slug→date map), not one `git log -1 --pretty=%cI <file>`
  subprocess per page. Per-file invocation is O(pages) subprocess spawns and is the
  documented slow path (withastro/astro#16803); Starlight's `lastUpdated` (D7)
  already does a bulk walk for the same data. The per-page frontmatter date
  override (FR-017) is applied on top of the map. This keeps build cost flat as the
  page set grows and is a build-only cost (zero served/runtime cost). The git
  invocation also interacts with the docs-site safe-aids guard
  (`validate-doc006-safe-aids.mjs` flags `child_process`); confirm the sitemap
  config path is within the guard's allowed surface during implementation.
- **Sitemap `<lastmod>` for a page with no commit history (FR-017 edge).** The bulk
  `git log --name-status` walk OMITS any file with no commit history (a brand-new
  uncommitted page, or one absent on a shallow→deep clone) — verified against
  Starlight's `getAllNewestCommitDate`, which never adds a map entry for an unseen
  file. The custom `serialize()` MUST therefore resolve such a page's `lastmod` as:
  (1) an explicit frontmatter date if the page pins one; (2) otherwise leave the
  entry's `lastmod` **undefined** so `@astrojs/sitemap` omits the `<lastmod>` element
  for that URL (spec-valid — `<lastmod>` is optional in the sitemap protocol). It
  MUST NOT default to `new Date()` / build time, and MUST NOT let `@astrojs/sitemap`'s
  build-time `lastmod` option fill it in (do not set the integration's top-level
  `lastmod` option). For the matching visible stamp, prefer a frontmatter
  `lastUpdated`/date on a new page; absent one, the stamp is simply not shown
  (Starlight's per-file commit-date lookup THROWS on a file with no timestamp, so the
  per-file path is NOT used for these — the frontmatter override is the supported
  remedy). This keeps the visible date and the sitemap `<lastmod>` consistent on the
  no-history path (FR-017, FR-018, SC-007).
- **`robots.txt` Sitemap line derivation.** The `Sitemap:` absolute URL is built from
  `site`+`base` at build time. If that derivation cannot produce a valid absolute URL,
  the endpoint MUST fail the build (a thrown error in the prerendered route) rather
  than emit a policy with a blank/missing `Sitemap:` line — `site`+`base` are
  statically configured (Constraints), so this is a build-time invariant, never a
  runtime path.

## Complexity Tracking

The only deviation from the constitution's nominal *file-count* thresholds is the
recorded reviewability-budget tension (13 estimator-production files / ~33 total
vs. the 8/25 block lines), which the reviewable-LOC ceiling (~300–360 < 400) and
the resolved one-spec decision justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| File count over the 8 production / 25 total *block* lines | The SEO surface is intrinsically multi-endpoint (robots, per-page `.md`, OG route, sitemap, structured data) on one shared `astro.config.mjs` + route-data surface; 4 of the 13 are test specs and 12 are one-line content edits | Splitting into 2 specs (the A/B seam) would create two PRs both editing `astro.config.mjs` and the shared route-data middleware — an artificial seam with merge-conflict risk; the reviewable-LOC (~300–360) stays under the 400 warn line, so the work is atomically reviewable as one slice. The A/B split remains the documented PR-emission fallback if the post-Tasks atomicity classifier recommends it. |
