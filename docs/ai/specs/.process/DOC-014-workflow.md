# SpecKit Workflow: DOC-014 — SEO and AI discoverability

**Template Version**: 1.0.0
**Created**: 2026-06-25
**Purpose**: Execution workflow for DOC-014. The phase prompts below were enriched from the Grill Me interview at scaffold time; copy-paste them into the autopilot / your AI coding agent as you execute each phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/DOC-014-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping. Three decisions deliberately **diverge** from the
roadmap text / sibling site — keep them in view:

1. **Allow AI training crawlers** (GPTBot, Google-Extended, CCBot, anthropic-ai,
   ClaudeBot) — the sibling blocks them; we take a max-discoverability posture (Q1).
2. **Use `starlight-llms-txt`** (Starlight-native) rather than porting the sibling's
   `@4hse/astro-llms-txt` (Q3).
3. **Per-page dynamic OG cards** rather than the sibling's single static card (Q6).

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | G1 pass, 0 clarification markers; 29 FR / 6 US / 18 AC / 10 SC |
| Clarify | `/speckit-clarify` | ✅ Complete | G2 pass; 3 sessions, 4 consensus resolutions. Key: custom `.md` endpoint, route-middleware JSON-LD, Person=F.Gabelmann, astro-og-canvas, git-lastmod serialize, retarget DOC-011 robots gate, fetch-depth:0 |
| Plan | `/speckit-plan` | ✅ Complete | G3 pass; 5 artifacts + 11 contracts (C1–C11), 6 entities, all 29 FR/10 SC traced. Advisory LOC estimate `pass` (proj 520 mechanical; real reviewable ~300–360 < 400). |
| Checklist | `/speckit-checklist` | ✅ Complete | G4 pass; 3 domains, 81 items, 27 gaps all remediated, 0 unresolved. Spec/plan hardened (single-source robots, publisher@id invariant, bulk git-log sitemap, no-history lastmod omission, fail-loud all surfaces). |
| Tasks | `/speckit-tasks` | ✅ Complete | G5 pass; 34 tasks (T001–T035), 8 `[P]`, 9 phases, all US1–US6 + D1–D12 covered. Atomicity route = one-navigable-PR (no split). |
| Analyze | `/speckit-analyze` | ✅ Complete | G6 pass (0 CRITICAL/HIGH); G6.5 confidence NO_DATA→soft-skip (advisory). 0 unresolved → consensus skipped. 5 findings remediated (2 MEDIUM + 3 LOW). All 7 divergences/constraints intact; 100% SC/US/contract/entity coverage. |
| Implement | `/speckit-implement` | ✅ Complete | G7 pass (34/34 tasks). 6 work-packages, all TDD-verified. `pnpm --dir docs-site validate` green (88/88 e2e). 5 source files + 6 e2e specs + 19 descriptions + CI fetch-depth + metric doc. |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

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

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| VI. KISS, Simplicity & YAGNI | Simplest approach that ships the SEO surface; no speculative config | Plan + code review |
| II. Script Safety | Any new bash (none expected) uses `set -euo pipefail`; docs-site validators are JS ESM | `bash -n` / `pnpm --dir docs-site validate` |
| IV. Test Coverage | New behavior is e2e-tested (port sibling `seo-*.spec` patterns); docs validation green | `pnpm --dir docs-site validate` + `validate:smoke` |
| V. Conventional Commits | PR title `feat(...)` / `docs(...)`, public-readable plain English | CI `validate-pr-title` |

**Constitution Check:** ✅ initial (Specify) — spec aligns with KISS (one spec, no split), test coverage (e2e planned for every SEO surface), and conventional-commits PR policy. Full command verification (`pnpm --dir docs-site validate` / `build` / `validate:smoke`) runs at the Implement gate.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-014 |
| **Name** | SEO and AI discoverability |
| **Branch** | `doc-014-seo-and-ai-discoverability` |
| **Dependencies** | DOC-011 (GitHub Pages deploy + noindex staging foundation already shipped) |
| **Enables** | Public launch (DOC-012); DOC-017 (Lighthouse/perf budget depends on DOC-014) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] All ~19 content pages carry `description:` frontmatter; `validate-docs-quality.mjs` requires its presence; a "refresh meta descriptions" task is recorded in DOC-015's scope.
- [ ] A 3-tier `robots.txt` is served (Astro endpoint): citation/retrieval bots allowed, **AI training bots also allowed**, default-allow `*`, with a `Sitemap:` directive.
- [ ] `starlight-llms-txt` emits `llms.txt` / `llms-full.txt` / `llms-small.txt`, documented as a coding-agent retrieval aid.
- [ ] A per-page raw Markdown (`.md`) variant is served at build time for coding-agent retrieval.
- [ ] JSON-LD `@graph` emits Organization (`@id` + `sameAs` → GitHub org) + WebSite + `SoftwareApplication` (per plugin page, `offers.price: 0`) + a Person/author entity, injected the Starlight way.
- [ ] Per-page Open Graph cards are generated at build time; OG/canonical metadata is correct for the staging `site` and finalizes automatically when DOC-012 flips the domain.
- [ ] Sitemap `<lastmod>` and a visible "Last updated" stamp derive from git commit date (Starlight `lastUpdated`, frontmatter override allowed) — never build time.
- [ ] The AI-discoverability success metric and its measurement source (GSC Generative AI reports + GA4 AI-referrer channel group) are documented, with no numeric target.

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/doc-014-seo-and-ai-discoverability/spec.md`

### Specify Prompt

```bash
/speckit-specify Make the Astro/Starlight docs site indexable, shareable, and discoverable across classic search and AI answer engines, with correct metadata for the eventual production domain.
```

#### Detailed Prompt

```bash
/speckit-specify

## Feature: SEO and AI discoverability (DOC-014)

### Problem Statement
The docs site is deployed to a noindex'd github.io staging URL with zero SEO metadata:
0 of ~19 content pages have meta descriptions, there is no Open Graph setup, no
production-grade robots.txt, no llms.txt, no JSON-LD, and no git-sourced freshness
signal. Before public launch (DOC-012) the site must be discoverable by both classic
search and AI answer/coding engines.

### Users
- Search engines and AI answer engines (ChatGPT Search, Perplexity, Google AI Overviews,
  Claude) — win citation via crawler access + entity clarity.
- Coding agents (Cursor, Claude Code, Copilot) — served by llms.txt tiers AND per-page .md.
- Humans sharing docs pages on social — served by per-page Open Graph cards.

### User Stories
- [US1] A citation crawler can fetch any page (robots.txt allows the citation tier).
- [US2] An AI training crawler can fetch any page (max-discoverability posture — DELIBERATE
  divergence from the sibling site, which blocks the training tier).
- [US3] A coding agent retrieves whole-site content (llms.txt/llms-full.txt) and a single
  page cheaply (per-page .md).
- [US4] A search engine reads correct meta descriptions, canonical URLs, JSON-LD entity
  graph, and a git-accurate sitemap lastmod for every page.
- [US5] A shared page renders a per-page Open Graph card.
- [US6] A maintainer can verify the "AI-discoverable" goal against a documented metric.

### Constraints
- Astro 6.4.6 + Starlight 0.40.0, pnpm 10.25.0, Node >=22.12. Rely on Starlight's built-in
  canonical + `lastUpdated`; do NOT add `astro-seo` (double-emits canonical).
- Keep `site` at the github.io staging value; DOC-012 owns the launch flip to
  plugins.racecraft.co. The DOC-011 noindex guard stays until DOC-012.
- All JSON-LD justified as Google/Bing rich-results + entity disambiguation, NOT as an
  LLM-citation lever (LLMs strip JSON-LD and read visible HTML).
- One spec, no split (~250-300 reviewable LOC; within the ~400 ceiling).

### Out of Scope
- Blocking AI training crawlers (deliberately allowed).
- Prose rewrites / answer-first restructuring / voice-tone (DOC-015 / DOC-019).
- Analytics activation + 404/legal/launch-hygiene (DOC-018).
- A numeric success-metric target (deferred to post-launch baseline).
- FAQPage/HowTo rich-result schema (sunset); `Accept: text/markdown` content negotiation
  (no crawler honors it on Astro static); cosmetic lastmod bumping; the production-domain
  flip (DOC-012).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 29 (FR-001–FR-029; incl. 6 scope-boundary negatives FR-024–029) |
| User Stories | 6 (US1-US6; P1: US1/US4, P2: US2/US3, P3: US5/US6) |
| Acceptance Criteria | 18 acceptance scenarios + 10 measurable success criteria (SC-001–SC-010) |

### Files Generated

- [x] `specs/doc-014-seo-and-ai-discoverability/spec.md`
- [x] `specs/doc-014-seo-and-ai-discoverability/checklists/requirements.md` (requirements quality checklist, all-pass)

---

## Phase 2: Clarify

**When to run:** Spec has areas open to interpretation. Max 5 targeted questions per session.
Seed these sessions from the design-concept **Open Questions** (the two plugin-selection
choices are the live ambiguities; the design decisions themselves are settled).

### Clarify Prompts

#### Session 1: Crawler & agent access

```bash
/speckit-clarify Focus on crawler/agent access: confirm the robots.txt 3-tier taxonomy with the training tier ALLOWED (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) plus the citation tier (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User) and default-allow *; which Starlight per-page-.md plugin to adopt (starlight-md-txt vs astro-markdown-for-agents) and whether it composes with starlight-llms-txt and starlight-links-validator without build conflict.
```

#### Session 2: Structured data & metadata

```bash
/speckit-clarify Focus on structured data: how to inject the JSON-LD @graph under Starlight (global head: config for Organization + WebSite vs a Head.astro component override for per-page SoftwareApplication + Person); which pages count as "plugin pages" for SoftwareApplication (currently only speckit-pro); the Organization @id + sameAs target (GitHub org); and the exact meta-description authoring approach for ~19 pages plus the validate-docs-quality.mjs presence rule.
```

#### Session 3: Build integration & freshness

```bash
/speckit-clarify Focus on build integration: which per-page OG approach (astro-og-canvas + Starlight component override per HiDeoo's recipe vs the starlight-og plugin) integrates cleanly with the existing passthroughImageService and brand assets; how to source sitemap <lastmod> from git via Starlight lastUpdated plus a sitemap serialize function (with frontmatter override); and confirmation that canonical relies solely on Starlight's built-in (no astro-seo).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Crawler & agent access | 5 (Q1–Q5) | **Q1 (CRITICAL, decided):** `validate-docs-quality.mjs` `validateStagingIndexingGuard()` has TWO DOC-011 assertions — (a) `public/robots.txt` must byte-equal the `Disallow: /` block (line 426), and (b) the astro.config noindex meta guard (line 434). DOC-014 → **delete `public/robots.txt`, add `src/pages/robots.txt.ts` 3-tier endpoint, RETARGET assertion (a)** to the new policy, **KEEP assertion (b)** (noindex meta is the real indexing guard, FR-029). `public/robots.txt` would otherwise shadow the endpoint. **Q2 (decided):** taxonomy = training-allow (GPTBot/Google-Extended/CCBot/anthropic-ai/ClaudeBot — inverts the sibling) + citation-allow (OAI-SearchBot/ChatGPT-User/Claude-SearchBot/Claude-User/PerplexityBot/Perplexity-User) + default-allow `*` + `Sitemap:` derived from `site`+`base` (NOT `astro:env` — docs-site has none). **Q4 (confirmed):** whole-site digest = `starlight-llms-txt` v0.10.0 (peer Starlight ≥0.38, Astro ^6 — compatible). **Q5 (decided):** `@astrojs/sitemap` is transitive-only (not in package.json/config) → must be added explicitly (FR-004 + the Session-2 git-lastmod hook). **Q3 (RESOLVED via consensus, 2/2 high-confidence):** per-page `.md` = a **custom Astro endpoint** `src/pages/[...slug].md.ts` reading `getCollection('docs')` → emits each page's raw `body` as `text/markdown`. NO new dependency (KISS/YAGNI). Beats `starlight-dot-md` (3 stars, Starlight 0.40 compat unverified) and `starlight-md-txt` (unverifiable, `.md.txt` URL). `starlight-links-validator` validates HTML only → no collision; `starlight-llms-txt` emits only `.txt` → no overlap; `getCollection` guarantees FR-008 (no orphaned/missing variants). 2 MDX pages emit raw body incl. import/JSX — acceptable per FR-007 (plain text/Markdown, not rendered HTML). design-concept's `astro-markdown-for-agents` does not exist → dropped. |
| 2 | Structured data & metadata | 5 (Q1–Q5) | **Q1 (decided, refines Q5 mechanism):** inject all JSON-LD via a **route-data middleware** (`routeMiddleware: './src/routeData.ts'` + ported `src/lib/schema.ts`), NOT a `Head.astro` override — Starlight 0.40 docs call Head-override "a last resort" and recommend route middleware (v0.32+). Site-wide Organization+WebSite on every route; SoftwareApplication added when slug ∈ plugin-page allowlist; Person site-wide/on landing. Entity SET unchanged (Q5). **Q3 (decided):** "plugin page" for SoftwareApplication = `src/content/docs/index.mdx` (the landing page that describes speckit-pro + links to the repo), matched via an explicit allowlist map so a 2nd plugin is a one-line add. **Q4 (decided, CRITICAL wrinkle):** add `validateMetaDescriptions(diagnostics)` to `validate-docs-quality.mjs` (globs `src/content/docs/**/*.{md,mdx}`, fails on missing/empty `description:`). **7 of 19 pages are GENERATED** by `generate-reference-pages.mjs` → their `description:` MUST be emitted IN THE GENERATOR (hand-edits get wiped on `reference:generate`); the other 12 authored by hand. Adds `generate-reference-pages.mjs` to touched files. **Q5 (confirmed):** Organization `@id`=`<site>#organization`, name "Racecraft Lab", `sameAs`=["https://github.com/racecraft-lab"]; WebSite `@id`=`<site>#website`, `publisher`→org `@id`; all derived from `site`+`base` (DOC-012-flip-safe). **Q2 (RESOLVED via consensus, 2/2 high-confidence):** emit **Person = Fredrick Gabelmann**, `sameAs`=["https://github.com/fgabelmannjr"], `worksFor`→Organization `@id`, with `@id`=`<site>#person` (NO PII in the `@id` fragment per Yoast guidance; name/sameAs are fine). Settled user decision (design-concept Q5 + FR-015 MUST + SC-006); identity is the project's established public identity (sibling site + git author); schema.org-correct (Person→worksFor→Org, additive to Org-as-WebSite-publisher). FR-016 boundary confirmed correct (rich-results/entity-disambiguation, NOT an LLM-citation lever). |
| 3 | Build integration & freshness | 5 (Q1–Q5) | **Q8 (confirmed):** canonical = exactly ONE `<link rel=canonical>` from Starlight built-in (`site`+`base`); NO `astro-seo`, no 2nd source (FR-027). **Q7 (confirmed):** visible "Last updated" stamp = Starlight `lastUpdated: true` (frontmatter override). **Q3 (decided, CRITICAL):** Starlight `lastUpdated` does NOT feed the sitemap and `@astrojs/sitemap` emits no `lastmod` by default → FR-017 needs a custom `serialize()` that does its OWN per-file git lookup (`git log -1 --pretty=%cI <file>`), frontmatter date override honored. So FR-017 (sitemap lastmod) and FR-018 (visible stamp) are TWO independent wirings. **Q2 (decided):** OG card draws from a build-only `.ttf` display face + PNG mark under `src/assets/og/` (brand fonts are woff2-only + logo SVG-only — neither works with astro-og-canvas's skia renderer); these are generated/build inputs, excluded from reviewable LOC. **Q5 (decided, CI cross-spec):** `deploy-docs.yml` checks out at depth-1 (no `fetch-depth`) → git dates would collapse to the deploy commit in CI (SC-007 fails). DOC-014 SETS `fetch-depth: 0` (feature enables its own runtime precondition; DOC-011 already shipped). Flagged in PR per the CLAUDE.md CI-touch rule. **Q1 (RESOLVED via consensus, 2/2 high-confidence):** per-page OG = **`astro-og-canvas` v0.11.1** (maintained by delucis/withastro; devDep pins `astro ^6.4.6`) via an `OGImageRoute` endpoint `src/pages/og/[...slug].ts` + OG/twitter:image meta injected by the SAME route middleware as JSON-LD (HiDeoo recipe). Endpoint MUST be static (`export const prerender = true`). Card needs build-only `.ttf` font + PNG logo (woff2 fails on Astro path-rewrite per issue #77; canvaskit `MakeImageFromEncoded` is raster-only, no SVG). `passthroughImageService` is orthogonal (canvas/skia render path); links-validator treats `.png` routes as assets. `starlight-og` PROVEN non-existent (4 negative signals) → dropped. **Q4 (RESOLVED via consensus, high-confidence, source-read):** Starlight 0.40 DEFERS — `@astrojs/starlight/index.ts:107-109` guard adds its internal sitemap ONLY if no integration named `@astrojs/sitemap` exists. So promote `@astrojs/sitemap` (3.7.3, transitive today) to a direct dep + add to `integrations` with the custom git-lastmod `serialize`; Starlight skips its own. No duplicate-instance error. |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-014-seo-and-ai-discoverability/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Framework: Astro 6.4.6 with @astrojs/starlight 0.40.0 (static output)
- Package manager: pnpm 10.25.0 (run scoped: `pnpm --dir docs-site ...`); Node >=22.12
- Existing integrations: starlight-links-validator; passthroughImageService (DOC-013 SVG handling)
- Testing: Playwright 1.61.0 (Chromium-only smoke + e2e), validate-docs-quality.mjs (JS ESM)
- New integrations to add: starlight-llms-txt; a per-page-.md plugin (starlight-md-txt OR
  astro-markdown-for-agents — resolve in Clarify); a per-page OG generator (astro-og-canvas
  + component override OR starlight-og — resolve in Clarify); @astrojs/sitemap if not present

## Constraints
- Rely on Starlight's built-in canonical + lastUpdated. Do NOT add astro-seo (double canonical).
- Keep `site: 'https://racecraft-lab.github.io'` + `base: '/racecraft-plugins-public'`;
  DOC-012 flips the domain. Keep the DOC-011 noindex head guard untouched.
- Port the proven sibling artifacts where they port: the robots.txt 3-tier ENDPOINT
  (src/pages/robots.txt.ts) ports cleanly; the JSON-LD schema FACTORY functions port but the
  layout-based injection must be redone Starlight-style (head: config + Head.astro override).
- ~250-300 reviewable LOC; one spec, no split.

## Architecture Notes
- robots.txt: an Astro endpoint emitting training-allow + citation-allow + default-allow +
  Sitemap:. (DECISION Q1: allow training bots — divergence from sibling, which blocks.)
- JSON-LD: Organization (@id + sameAs → GitHub org) + WebSite global via Starlight head:;
  SoftwareApplication (offers.price 0) per plugin page + Person/author via Head.astro override.
  Justify as rich-results + entity disambiguation only. (DECISION Q5)
- llms.txt: starlight-llms-txt, NOT a port of @4hse/astro-llms-txt. (DECISION Q3)
- per-page .md: build-time distinct .md URLs (no Accept-header negotiation on Astro static).
  (DECISION Q4)
- OG: per-page dynamic cards at build time. (DECISION Q6)
- sitemap lastmod + "Last updated" stamp: git commit date via Starlight lastUpdated + a
  sitemap serialize function; frontmatter override allowed. (DECISION Q7)
- success metric: a documentation artifact defining GSC Generative AI reports + a GA4
  AI-referrer channel group; no numeric target. (DECISION Q9)

Re-read docs/ai/specs/.process/DOC-014-design-concept.md for the full rationale of each decision.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ | Technical context, execution flow, Declared File Operations, Complexity Tracking (reviewability tension recorded) |
| `research.md` | ✅ | D1–D12 decision rationales (design-concept citations carried) |
| `data-model.md` | ✅ | 6 entities (content page, crawler policy, structured-data graph, agent content, sitemap, metric def) |
| `contracts/` | ✅ | `build-output-contracts.md` C1–C11, each mapped to FRs + SCs + verification layer |
| `quickstart.md` | ✅ | How to verify SEO surfaces locally |

**Planning findings to carry into Tasks/Implement (all surfaced, none blocking):**
1. CI checkout is `actions/checkout@…v7.0.0` (not v4) — add `fetch-depth: 0` to that step.
2. **3 MDX pages**, not 2 (`index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`) — raw body acceptable per FR-007.
3. **`playwright.config.mjs` pins `testMatch: 'docs-smoke.spec.mjs'`** — MUST broaden to a glob or the 4 new SEO specs won't execute (required surgical edit).
4. CI installs `--frozen-lockfile` → the regenerated `docs-site/pnpm-lock.yaml` MUST be committed or the deploy job fails (declared MODIFIED, excluded from prod-LOC).
5. `reference.md` is hand-authored → split is 12 hand-authored + 7 generated = 19; `0/19` have `description:` today (SC-003 baseline); the generator's `renderPage()` already has a `description` field (emit it as frontmatter — one-line change).
6. doc-014 worktree `docs-site/node_modules` likely NOT installed — Implement runs `pnpm --dir docs-site install` after adding deps (`starlight-llms-txt`, `astro-og-canvas` + `canvaskit-wasm`, promote `@astrojs/sitemap`).

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates spec AND plan together.

### Recommended Domains

Target 2-3. Chosen from the spec's risk surface:

#### 1. seo-metadata Checklist (custom domain)

Why this domain: the spec's core risk is metadata correctness — description presence,
canonical URLs, JSON-LD validity, OG tag completeness, robots.txt taxonomy, and sitemap
lastmod accuracy. This is where silent SEO defects hide.

```bash
/speckit-checklist seo-metadata

Focus on SEO and AI discoverability requirements:
- robots.txt 3-tier taxonomy is correct AND ordered (training-allow + citation-allow + default-allow + Sitemap:)
- JSON-LD @graph is valid and the WebSite publisher @id matches the Organization @id; SoftwareApplication carries offers.price 0
- Canonical relies solely on Starlight built-in (no astro-seo double-emit); URLs derive from `site` + `base`
- Every content page has a non-empty `description:`; the validator rejects a missing one
- Pay special attention to: the deliberate divergences (training bots ALLOWED; starlight-llms-txt not the @4hse port; per-page dynamic OG not static) being reflected, not silently reverted
```

#### 2. performance Checklist

Why this domain: per-page OG generation + three new build integrations + a sitemap
serialize function all affect build cost and Core Web Vitals — and DOC-017 will gate
Lighthouse, so DOC-014 must not regress build/runtime perf.

```bash
/speckit-checklist performance

Focus on SEO and AI discoverability requirements:
- Per-page OG image generation does not blow up build time or output size for ~19-26 pages
- New integrations (starlight-llms-txt, per-page .md, OG generator) do not add render-blocking assets
- The static-output build stays within reasonable bounds ahead of DOC-017's Lighthouse budget
- Pay special attention to: build-time cost of dynamic OG and per-page .md generation
```

#### 3. error-handling Checklist

Why this domain: the robots.txt endpoint, build-time OG generation, per-page .md
generation, and git-sourced lastmod each have failure modes (missing git history, missing
frontmatter, generation errors) that must degrade safely.

```bash
/speckit-checklist error-handling

Focus on SEO and AI discoverability requirements:
- lastmod when a file has no git history yet (new page) — frontmatter override / sensible fallback
- OG/.md generation failure for one page does not fail the whole build silently
- robots.txt endpoint always emits a valid response
- Pay special attention to: missing `description:` and missing `lastUpdated` edge cases
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| seo-metadata | 41 | 4 (all remediated, 0 unresolved → consensus skipped) | FR-001/002/003/004/**004a**(new)/010/011/012/**013**(extended)/014/024/027 + new "full git history at build" assumption |
| performance | 20 | 11 (all remediated, 0 unresolved → consensus skipped) | plan.md Performance Goals/Constraints + spec "build-time cost" assumption. **KEY:** sitemap `serialize()` MUST use a single bulk `git log` walk (slug→date map), not per-page subprocess (O(pages) slow path); carry as a Tasks constraint. OG/.md/llms costs proportionate, no caching (KISS). |
| error-handling | 20 | 12 (all remediated, 0 unresolved → consensus skipped) | FR-017/FR-018 tightened + 2 new edge cases + plan "Build-failure posture (all surfaces, never silent)". **No-git-history `lastmod`:** (1) frontmatter date if pinned, else (2) OMIT `<lastmod>` (spec-valid, never build time); visible stamp follows same order. |
| **Total** | 81 | 27 (all remediated, 0 unresolved → all 3 consensus tasks skipped) | seo-metadata 41 / performance 20 / error-handling 20 |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/doc-014-seo-and-ai-discoverability/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; clear acceptance criteria referencing FR-xxx
- Dependency ordering: config/integrations -> components/endpoints -> content frontmatter -> validators/tests
- Mark parallel-safe tasks with [P]
- Organize by user story (US1-US6), not by technical layer

## Implementation Phases
1. Foundation: add integrations (starlight-llms-txt, per-page .md plugin, OG generator, sitemap) to astro.config; wire Starlight lastUpdated
2. US1/US2/US3 (crawler + agent access): robots.txt endpoint (training-allow), llms.txt verify, per-page .md verify
3. US4/US5 (metadata): JSON-LD @graph (Org/WebSite/SoftwareApplication/Person) via head:/Head.astro; per-page OG; sitemap git-lastmod serialize; ~19 description: frontmatter + validate-docs-quality.mjs rule
4. US6 + polish: success-metric definition doc; "Last updated" stamp; cross-cutting verification

## Constraints
- Tests live in docs-site/tests/ (Playwright Chromium-only); port the sibling e2e patterns:
  seo-robots-txt.spec, seo-schema-org.spec, seo-llms-txt.spec, seo-sitemap.spec
- Bound tasks by the Non-goals in the design concept: do NOT block training bots, do NOT add
  astro-seo, do NOT flip the production domain, do NOT author a numeric metric target,
  do NOT rewrite prose (DOC-015)
- Add a "refresh meta descriptions" task reference into DOC-015's scope (cross-spec note, Q2)
- Reference docs/ai/specs/.process/DOC-014-design-concept.md for the "why" behind each decision
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 34 (T001–T035, incl. T009A + T012a) |
| **Phases** | 9 (Setup, Foundational, US1–US6, Polish) |
| **Parallel Opportunities** | 8 `[P]` (T003, T005, T006, T010, T013, T014, T017, T023) |
| **User Stories Covered** | US1–US6 (US1=4, US2=2, US3=3, US4=8, US5=2, US6=1; 14 unlabelled Setup/Foundational/Polish) |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. Leave blank during scoping.

The slice-sizing branch (design concept Q10) chose **one spec, no split** (~250-300 LOC,
within the ~400 ceiling). The classifier may still recommend a split-PR emission based on
structural seams; the documented fallback seam is (A) crawler/agent access [robots.txt +
llms.txt + per-page .md] vs (B) discoverability metadata [descriptions + JSON-LD + OG +
sitemap lastmod + metric].

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | The structural-seam classifier found no safe split; ship as one reviewable PR (matches design-concept Q10 "one spec, no split"). |
| **Releasable** | `true` | Additive change; no destructive migration or concurrency sensitivity. |
| **Signals** | `change-shape:modify-heavy` | Touches one cohesive site-config/head surface; the A/B seam (crawler-access vs metadata) was considered and rejected as artificial (both halves edit `astro.config`). |
| **Warnings** | none | — |

### Reviewability gate (tasks mode) — size-only block, NOT a re-slicing stop

`reviewability-gate.sh tasks` returned `status: block` (`reviewable_loc:1360`, `production_files:14`, `total_files:130`, `primary_surfaces:6`). This is the documented **coarse heuristic over-count**, not a real over-budget:
- `reviewable_loc:1360` = tasks(34)×40, a flat heuristic; the Plan-phase estimator (which reads the Declared File Operations) returned `pass` with real reviewable ≈ 305–360 LOC (< 800 block, < 400 warn).
- `total_files:130` = path-token grep counting every file path mentioned across 34 task descriptions (many repeated); the real touched-file set is ~14 code files + 19 one-line `description:` additions + generated outputs (excluded per Reviewability Notes).
- `production_files:14` is real but cohesive (5 new src + 5 modified + 4 test specs), all SEO wiring on one config/head surface.

**Resolution:** per the skill, a valid current **size-only** block is not a manual re-slicing stop. The atomicity classifier (structural seams) returned `one-navigable-PR`, so there is no safe split. Proceed as one navigable PR; the authoritative size check is the PR-time **diff-mode** gate (`final-reviewability-backstop.sh`), which measures the real diff with generated/lockfile exclusions. The PR packet will lead reviewers through a navigable review order.

## Layer Plan

`layer_plan.status = skipped` — atomicity route is `one-navigable-PR` (non-split), so the PRSG layer planner (`plan-layers.sh`) does not run. No marker-based PR emission; single-PR path at post-implementation.

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-014-seo-and-ai-discoverability
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment — KISS/YAGNI (no speculative config), test coverage (e2e for every SEO surface)
2. Coverage gaps — every FR and user story (US1-US6) has a task
3. Consistency between task file paths and the actual docs-site structure
4. DESIGN-CONCEPT DRIFT — flag any downstream artifact that contradicts the design concept's
   decisions. The design concept is the source of truth for scoping. Specifically verify these
   three divergences are intact (a downstream artifact that reverts them is WRONG unless it
   carries an explicit revision note):
   - Q1: AI TRAINING bots are ALLOWED (not blocked like the sibling)
   - Q3: llms.txt uses starlight-llms-txt (NOT a port of @4hse/astro-llms-txt)
   - Q6: Open Graph is PER-PAGE DYNAMIC (not a single static card)
   Also verify: no astro-seo dependency (Q8); no numeric metric target (Q9); JSON-LD justified
   as rich-results/entity-disambiguation only, never as LLM-citation (Q5).
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| C1 | MEDIUM | FR-016 (JSON-LD justified as rich-results/entity-disambiguation, not LLM-citation) had no producing task | Folded into T030 + cited FR-016/C2 (the success-metric doc now carries the justification) |
| F1 | MEDIUM | Contract C7 + data-model §5 showed the per-file `git log` command the plan/T021 forbid | Updated C7 + data-model §5 to the single bulk `git log` walk wording (+ no-history OMIT) — now consistent with plan/T021 |
| Cv1 | LOW | FR-026 covered only by the range phrase in T033, not its explicit ID | Made all FR-024..029 + FR-023 boundaries explicit in T033 |
| Cv2 | LOW | Design-concept OG Open Question not stamped RESOLVED (downstream already landed on astro-og-canvas) | Added the RESOLVED note to the design-concept Open Question for provenance |
| Cv3 | LOW | Task IDs skip T007/T008/T009 (T009A present) | Informational — intentional template artifact for the reviewability-budget gate task; no broken cross-references |
| — | — | **Coverage** | FR 29/30 task-covered (FR-016 closed by C1); SC 10/10; US 6/6; contracts C1–C11 11/11; entities 6/6. 0 ambiguity, 0 duplication, 0 CRITICAL. |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First
For each task: RED (failing test) -> GREEN (minimum impl) -> REFACTOR -> VERIFY.

### Pre-Implementation Setup
1. `pnpm --dir docs-site install` (after adding integrations)
2. `pnpm --dir docs-site validate` passes before changes
3. Confirm you are on branch `doc-014-seo-and-ai-discoverability`

### Implementation Notes
- Port the proven sibling test patterns into docs-site/tests/ (Chromium-only):
  seo-robots-txt.spec (assert training tier ALLOWED here — the inverse of the sibling),
  seo-schema-org.spec (Organization @id == WebSite publisher @id; SoftwareApplication offers.price 0; Person present),
  seo-llms-txt.spec (llms.txt/llms-full.txt/llms-small.txt 200 + non-empty),
  seo-sitemap.spec (lastmod is a valid ISO date sourced from git, not build time)
- robots.txt: port src/pages/robots.txt.ts but MOVE the training tier from Disallow to Allow (Q1)
- JSON-LD: port schema.ts factory functions; redo injection Starlight-style (head: + Head.astro)
- Consult docs/ai/specs/.process/DOC-014-design-concept.md Q&A for the "why" behind edge-case handling
- Decisions in the design concept not reflected in tasks.md are gaps — surface them before coding
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| WP1 - Foundation (deps/config/skeletons) | T001-T006, T009A | ✅ | astro-og-canvas+canvaskit, starlight-llms-txt, @astrojs/sitemap; schema.ts + routeData.ts skeleton; `astro check` clean |
| WP2 - Crawler & agent access (US1/US2) | T010-T012a, T015-T016, T031 | ✅ | robots.txt.ts 3-tier (training inverted); DOC-011 gate retargeted, noindex kept; 14/14 e2e |
| WP3 - Agent content (US3) | T017-T019 | ✅ | per-page .md endpoint (19=1:1); 3 llms digests; 6/6 e2e |
| WP4 - Metadata & structured data (US4) | T013-T014, T020-T025 | ✅ | JSON-LD (publisher@id==Org@id, Person, SoftwareApplication@index); git-lastmod bulk-walk; 19 descriptions + gate; 10/10 e2e + negative gate test |
| WP5 - Open Graph cards (US5) | T003, T028-T029 | ✅ | astro-og-canvas OGImageRoute (19 PNGs); og/twitter:image (no dup twitter:card); 4/4 e2e |
| WP6 - Metric doc + polish | T026-T027, T030, T032-T035 | ✅ | success-metric doc (no numeric target); deploy fetch-depth:0; DOC-015 refresh handoff; full validate 88/88 |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Docs validation passes: `pnpm --dir docs-site validate`
- [ ] Smoke + e2e pass: `pnpm --dir docs-site validate:smoke`
- [ ] Build succeeds: `pnpm --dir docs-site build`
- [ ] robots.txt served with training tier ALLOWED + citation tier ALLOWED + Sitemap:
- [ ] JSON-LD validates; sitemap lastmod is git-sourced; per-page OG + .md present
- [ ] All ~19 pages have `description:`; validator rejects a missing one; DOC-015 refresh task recorded
- [ ] Success-metric definition documented (no numeric target)
- [ ] noindex staging guard untouched; `site` unchanged (DOC-012 owns the flip)
- [ ] PR created with a public-readable conventional-commits title and reviewed

---

## Self-Review (Post-Implementation, 4-question audit)

1. **Fully implements the spec?** Yes. All 29 FRs + 10 SCs covered and verified: 3-tier robots (FR-001–004a / SC-001/002), llms.txt + per-page `.md` (FR-006/007/008 / SC-005), descriptions + presence gate (FR-009/010 / SC-003), exactly one canonical (FR-011/027 / SC-004), JSON-LD graph with publisher@id==Org@id + SoftwareApplication on the landing page + Person (FR-013/014/015 / SC-006), git-sourced sitemap lastmod + visible stamp (FR-017/018 / SC-007), per-page OG cards (FR-019/020 / SC-008), success-metric doc with no numeric target (FR-021/022/023 / SC-009), staging URLs with no hardcoded prod domain (FR-012 / SC-010), negatives FR-024–029 honored. `pnpm --dir docs-site validate` green (88/88).
2. **Shortcuts / tech debt?** (a) OG cards are text-only (no logo raster) — acceptable per FR-019 (per-page titled card); a logo PNG can be added later. (b) The 3 SEO e2e specs hardcode the staging absolute URL — must flip in lockstep at the DOC-012 launch (handoff flagged in the PR body). (c) A typed `infra` reviewability exception was taken because the change is one cohesive, unsplittable surface (atomicity = one-navigable-PR). No silent debt.
3. **Test coverage adequate?** Strong. 6 Playwright e2e specs (robots, llms+md, schema, sitemap, og) + the `validateMetaDescriptions` gate (with a verified negative test) + the existing DOC-010 smoke suite. The sitemap spec proves git-sourcing (not build time) via an unmodified page's real commit date.
4. **What should a reviewer look at first?** PR size (1321 reviewable LOC; ~615 are tests) — see the infra-exception rationale; the DOC-011 robots quality-gate retarget (noindex meta kept intact); the `deploy-docs.yml` `fetch-depth: 0` CI touch (no CLAUDE.md CI/CD-section update needed — checkout-depth only); and the all-identical sitemap `lastmod` today (real — every page got its `description` in one commit; the test guards via untouched pages).

---

## Consensus Resolution Log

| Phase | Item | Category | Round | Analysts | Outcome | Confidence |
|-------|------|----------|-------|----------|---------|------------|
| Clarify S1 | Q3: per-page `.md` serving approach | [domain],[codebase] | 1 | domain-researcher + codebase-analyst | **Custom Astro endpoint** `src/pages/[...slug].md.ts` (getCollection→raw body, no new dep). Beat `starlight-dot-md` / `starlight-md-txt`. | High (2/2 agree) |
| Clarify S2 | Q2: Person/author identity (FR-015) | [spec],[ambiguous] | 1 | spec-context-analyst + domain-researcher | **Emit Person = Fredrick Gabelmann**, `sameAs` github.com/fgabelmannjr, `worksFor`→Org, `@id`=`<site>#person` (no PII in `@id`). Settled by design-concept Q5 + FR-015; schema.org-correct. | High (2/2 agree) |
| Clarify S3 | Q1: per-page OG generation approach | [domain],[ambiguous] | 1 | domain-researcher + codebase-analyst | **`astro-og-canvas` v0.11.1** + `OGImageRoute` endpoint + route-middleware injection (static `prerender`). Needs build-only `.ttf`+PNG assets. `starlight-og` proven non-existent. | High (2/2 agree) |
| Clarify S3 | Q4: `@astrojs/sitemap` duplicate-instance on Starlight 0.40 | [codebase],[domain] | 1 | domain-researcher + codebase-analyst | **Starlight 0.40 DEFERS** (guard at `index.ts:107-109`) → add standalone `@astrojs/sitemap` + custom git-lastmod `serialize`; no error. | High (source-read) |

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```
docs-site/
├── astro.config.mjs              # site/base, integrations (Starlight, llms-txt, .md, OG, sitemap)
├── src/
│   ├── content/docs/**           # ~19 content pages (add description: frontmatter)
│   ├── components/                # Head.astro override (JSON-LD @graph injection)
│   └── pages/robots.txt.ts        # new — 3-tier endpoint (training tier ALLOWED)
├── public/robots.txt              # DOC-011 staging guard (replaced by the endpoint)
├── scripts/validate-docs-quality.mjs  # add description-presence rule
└── tests/                         # Playwright e2e (port sibling seo-*.spec patterns)
specs/doc-014-seo-and-ai-discoverability/
├── SPEC-MOC.md                    # navigation marker (committed at scaffold)
├── spec.md / plan.md / tasks.md   # generated by the phases above
```

---

Populated from the DOC-014 Grill Me interview (2026-06-25). The design concept doc at
`docs/ai/specs/.process/DOC-014-design-concept.md` is the source of truth for every scoping decision.

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=speckit-pr-packet --> Blocked PR packet validation for `speckit-pr-packet`; result `specs/doc-014-seo-and-ai-discoverability/.process/pr-packets/speckit-pr-packet/validation.json`; rules: `unknown`.
