---
description: "Task list for DOC-014 — SEO and AI Discoverability"
---

# Tasks: SEO and AI Discoverability

**Input**: Design documents from `/specs/doc-014-seo-and-ai-discoverability/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md (D1–D12), data-model.md (6 entities), contracts/build-output-contracts.md (C1–C11)

**Tests**: REQUESTED. This feature ships 4 Playwright e2e specs (Chromium-only) plus a new `validate-docs-quality.mjs` rule (D12, C1/C2/C5/C7/C9). Test tasks are therefore included and, per TDD, are authored before or alongside the behavior they verify.

**Reviewability**: The plan ratifies ONE spec (Constitution Check → "Split decision: remains ONE spec"). Reviewable LOC ~300–360 (under the 400 warn line). The mechanical estimator trips the file-/total-count block lines (13 production files / ~33 total), explained by the estimator's `files×40` heuristic over 4 test specs + 12 one-line content edits; this tension is surfaced (not silently passed) and the documented A/B fallback split (A: crawler/agent access; B: metadata/structured-data/cards/sitemap/metric) is the PR-emission fallback ONLY if the post-Tasks atomicity classifier recommends it. T009A records this verdict before implementation.

**Organization**: Tasks are grouped by user story (US1–US6) so each discovery surface can be implemented and tested independently. The "why" behind each decision is in `docs/ai/specs/.process/DOC-014-design-concept.md` (Q1–Q10) and `research.md` (D1–D12).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)
- All paths are repo-relative to the worktree root; `docs-site/` is the static-site surface.

## Path Conventions

- Static documentation site: `docs-site/src/`, `docs-site/scripts/`, `docs-site/tests/`
- CI: `.github/workflows/`
- Success-metric doc: `docs/ai/specs/`
- All absolute URLs derive from `site` (`https://racecraft-lab.github.io`) + `base` (`/racecraft-plugins-public`). The production domain MUST NOT be hardcoded (FR-012, D10).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the new dependencies and install them so the build can resolve the new integrations/plugins. No behavior yet.

- [x] T001 Add the three new direct dependencies to `docs-site/package.json`: `starlight-llms-txt` `0.10.0` (D4), `astro-og-canvas` `0.11.1` + `canvaskit-wasm` (D5), and promote `@astrojs/sitemap` `3.7.3` from transitive to a direct dependency (D6). Do NOT add `astro-seo` (FR-027, D10) or `schema-dts` (D2 — YAGNI). Keep `docs-site/package.json` `version` at `0.0.0` (no plugin version bump).
- [x] T002 Run `pnpm --dir docs-site install` to resolve the new deps (this worktree's `docs-site/node_modules` is absent — research.md "Cross-cutting facts"), then `pnpm --dir docs-site exec playwright install --with-deps chromium`. Confirm `docs-site/pnpm-lock.yaml` regenerates (it MUST be committed because CI installs with `--frozen-lockfile` — `deploy-docs.yml`; T035 re-verifies before hand-off).
- [x] T003 [P] Add the build-only Open Graph assets under `docs-site/src/assets/og/`: a `.ttf`/`.otf` display face and a PNG logo. CanvasKit/Skia rejects `woff2` and `SVG` (D5), so these formats are required. These are generated/binary build inputs excluded from the reviewable-LOC estimate (spec Reviewability Notes; plan "Declared File Operations").

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the shared `astro.config.mjs` surface (integrations, plugins, route middleware registration, `lastUpdated`) and create the shared module skeletons that multiple user stories depend on. This is the single shared config + head surface the plan cites as the reason the feature is one atomic slice.

**⚠️ CRITICAL**: No user-story endpoint behavior can be verified until this phase is complete — the integrations/plugins must be registered first.

- [x] T004 In `docs-site/astro.config.mjs`, additively wire all new build surfaces, preserving existing config (`site: 'https://racecraft-lab.github.io'`, `base: '/racecraft-plugins-public'`, `passthroughImageService()`, and the DOC-011 `noindex, nofollow` head meta — all untouched, FR-029): (a) add `@astrojs/sitemap` to `integrations` with a placeholder `serialize` hook filled in by T021 (D6); (b) add `starlight-llms-txt` to Starlight `plugins` (D4); (c) set Starlight `lastUpdated: true` (D7, FR-018); (d) register the route-data middleware via Starlight `routeMiddleware` pointing at `docs-site/src/routeData.ts` (D2). Do NOT set the sitemap integration's top-level `lastmod` option (the no-history fallback must be able to OMIT `<lastmod>`; plan implementation notes).
- [x] T005 [P] Create the shared schema-factory module `docs-site/src/lib/schema.ts` with typed object-literal factories ported in substance from the sibling (NO `schema-dts` dep): `buildOrganizationSchema`, `buildWebSiteSchema`, `buildSoftwareApplicationSchema`, `buildPersonSchema`, a `buildGraph` assembler, and a `pluginPages` allowlist map (slug → application metadata; currently only the landing-page slug `''` → SpecKit Pro). All `@id`/URL values derive from `site`+`base` (`SITE_BASE`), with NO PII in any `@id` fragment (data-model §3, D2). Used by US4 (structured data) and indirectly by US5 (same middleware). This is module scaffolding; the middleware that consumes it is T020.
- [x] T006 [P] Create the route-data middleware skeleton `docs-site/src/routeData.ts` (registered in T004) as a Starlight `defineRouteMiddleware` that will append the JSON-LD `<script>` (US4, T020) and the `og:image`/`twitter:image` head tags (US5, T029). Land the empty-but-wired middleware first so US4 and US5 extend one shared head-injection mechanism rather than adding a second (KISS, D2/D5). The JSON-LD body is added in T020; the OG tags are added in T029.
- [x] T009A Verify the reviewability budget against the planned task/file scope and record the split decision before implementation. Confirm: reviewable LOC stays ~300–360 (< 400 warn); the ratified ONE-spec decision (plan Constitution Check) holds; and the A/B fallback (A = crawler/agent access: robots.txt + llms.txt + per-page `.md`; B = metadata/structured-data/cards/sitemap/metric) is invoked ONLY if the post-Tasks `atomicity-route.sh` classifier recommends a split-PR emission. This is a downstream PR-emission decision, not a spec split. Record the verdict in the workflow evidence.

**Checkpoint**: `astro.config.mjs` registers sitemap + llms-txt + route middleware + `lastUpdated`; `schema.ts` and `routeData.ts` skeletons exist. User-story work can now begin.

---

## Phase 3: User Story 1 — Citation crawler can fetch any page (Priority: P1) 🎯 MVP

**Goal**: Publish a site-root crawler-access policy whose citation tier (`OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`) is explicitly allowed, the default `*` is allowed, and the absolute sitemap location is advertised — all derived from `site`+`base` (D1, C1).

**Independent Test**: Fetch `/robots.txt` and confirm each citation-tier user-agent gets `Allow: /`, default `*` is allowed, and a `Sitemap:` line points at `${SITE_BASE}/sitemap-index.xml` (spec US1 Independent Test; SC-001).

### Tests for User Story 1 ⚠️

> Write/author the test FIRST; it fails until T011 lands the endpoint.

- [x] T010 [P] [US1] Author `docs-site/tests/seo-robots-txt.spec.mjs` (Playwright, Chromium-only via `test.skip(browserName !== 'chromium')`, matching `docs-smoke.spec.mjs` style). Fetch `/robots.txt` via `request.get(...)` and assert: each citation-tier UA is allowed (US1/SC-001); each training-tier UA is **ALLOWED** — the inverse of the sibling's "blocked" assertion (US2/SC-002, covers Phase 4); default `*` is allowed (US1); a `Sitemap:` directive is present (FR-004); and `Disallow: /` appears for NO training-tier UA (C1). This single spec covers US1 + US2 (D12, C1).

### Implementation for User Story 1

- [x] T011 [US1] Create the dynamic endpoint `docs-site/src/pages/robots.txt.ts` emitting `text/plain; charset=utf-8`, HTTP 200, with `export const prerender = true`. Emit the 3-tier policy (data-model §2, C1): citation tier each `Allow: /`; default `User-agent: *` `Allow: /`; and a `Sitemap: ${SITE_BASE}/sitemap-index.xml` line built from `site`+`base` (NOT `astro:env` — none is configured, D1). If the `site`+`base` derivation cannot produce a valid absolute URL, throw (fail the build) rather than emit a blank `Sitemap:` line (plan implementation notes). The training tier is added in T015 (US2) — land the file here with citation + default + sitemap, then extend it in Phase 4. (FR-001, FR-003, FR-004, FR-004a)
- [x] T012 [US1] Delete the static `docs-site/public/robots.txt` (currently `User-agent: *\nDisallow: /`) so it cannot shadow the `robots.txt.ts` route at the same path (D1, C1, FR-004a).
- [x] T012a [US1] Retarget the robots assertion inside `validateStagingIndexingGuard()` in `docs-site/scripts/validate-docs-quality.mjs` (the `DOC011_STAGING_ROBOTS_*` constants ~line 69 and the assertion ~lines 423–430): assert the NEW 3-tier endpoint policy (citation/default allowed, Sitemap present) instead of the old static `public/robots.txt == Disallow: /` — otherwise `validate:quality` fails once `public/robots.txt` is deleted (T012). **KEEP the noindex-meta assertion intact** (~lines 432–438) — it is the real DOC-011 staging indexing guard and MUST remain (FR-029, C1, C10). This retargets ONLY the robots assertion; it does NOT weaken indexing posture.

**Checkpoint**: `/robots.txt` serves the citation-tier-allow + default-allow + sitemap policy; the quality gate's robots assertion now matches the endpoint policy while the noindex guard stays intact; `seo-robots-txt.spec.mjs` passes its US1 assertions. US1 is independently testable. (US2 assertions in the same spec pass after T015.)

---

## Phase 4: User Story 2 — AI training crawler can fetch any page (Priority: P2)

**Goal**: Extend the crawler-access policy so the AI-training tier (`GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot`) is explicitly allowed — a deliberate max-discoverability posture that INVERTS the sibling site, and record that decision so it is not "fixed" back (D1, FR-002, FR-005, FR-024).

**Independent Test**: Fetch `/robots.txt` and confirm each training-tier user-agent gets `Allow: /` (none gets `Disallow: /`); confirm the allow-training divergence is recorded in the feature documentation (spec US2 Independent Test + AS2; SC-002).

### Implementation for User Story 2

- [x] T015 [US2] Extend `docs-site/src/pages/robots.txt.ts` (from T011) to add the training tier — `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot`, each `Allow: /` — INVERTING the sibling `landing-page/website/src/pages/robots.txt.ts`, which `Disallow: /`s exactly these five (D1, data-model §2, C1). MUST NOT emit `Disallow: /` for any of them (FR-024). The training-tier ALLOWED assertion is already in `seo-robots-txt.spec.mjs` (T010), which now fully passes. (FR-002)
- [x] T016 [US2] Record the deliberate allow-training divergence from the sibling's blocking posture in the success-metric documentation artifact (the doc created in T030) so a future maintainer does not "fix" it back to a blocking default. (FR-005, US2 AS2, C11) — cross-references T030.

**Checkpoint**: `/robots.txt` now allows all three tiers; `seo-robots-txt.spec.mjs` fully passes; the allow-training rationale is recorded. US1 and US2 both work.

---

## Phase 5: User Story 3 — Coding agent retrieves whole-site and single-page content (Priority: P2)

**Goal**: Expose agent-readable content: the three whole-site `starlight-llms-txt` digests (wired in T004) and a per-page raw-Markdown variant served from a dependency-free custom endpoint, one per content page with no orphans (D3, D4, C4, C5).

**Independent Test**: Fetch `/llms.txt`, `/llms-full.txt`, `/llms-small.txt` (each 200 + non-empty) and a per-page `/<slug>.md` (returns that page's raw body as `text/markdown`); confirm one-to-one with `getCollection('docs')` (spec US3 Independent Test; SC-005).

### Tests for User Story 3 ⚠️

> Author FIRST; fails until the build emits the digests/variant.

- [x] T017 [P] [US3] Author `docs-site/tests/seo-llms-txt.spec.mjs` (Playwright, Chromium-only). Assert all three digest URLs (`/llms.txt`, `/llms-full.txt`, `/llms-small.txt`) return HTTP 200 with non-empty bodies (D12, C5, FR-006, SC-005).

### Implementation for User Story 3

- [x] T018 [US3] Create the per-page agent-readable endpoint `docs-site/src/pages/[...slug].md.ts` (NO plugin — D3). Read `getCollection('docs')`, return each entry's raw `body` as `text/markdown`, with `export const prerender = true` and `getStaticPaths` iterating the collection so there is exactly one `.md` per content page and no orphans (FR-007, FR-008, C4, SC-005). The 3 MDX pages emit raw `body` including `import`/JSX — acceptable per FR-007 (research D3). Distinct build-time URL (no `Accept`-header content negotiation — FR-028).
- [x] T019 [US3] Verify `starlight-llms-txt` (registered in T004) emits `/llms.txt`, `/llms-full.txt`, and `/llms-small.txt` from the site content model on `astro build`, and that the per-page `.md` variant and the `llms-full.txt` digest may overlap in content yet both remain individually fetchable and do not conflict at build time (spec Edge Case "Per-page text variant vs. whole-site digest overlap"; FR-006). Confirmed by `seo-llms-txt.spec.mjs` (T017) + a build.

**Checkpoint**: Three digests and per-page `.md` variants are fetchable; `seo-llms-txt.spec.mjs` passes. US3 is independently testable.

---

## Phase 6: User Story 4 — Search engine reads correct metadata for every page (Priority: P1)

**Goal**: Every content page carries a non-empty meta description, exactly one canonical URL (Starlight built-in, no second source), the structured-data entity graph (Organization + WebSite site-wide; SoftwareApplication on the landing page; Person), a git-accurate sitemap `<lastmod>` (single bulk `git log` walk, never build time), and a matching visible "last updated" stamp (D2, D6, D7, D9, D10, C2, C3, C7, C8, C9).

**Independent Test**: Crawl each content page and confirm a non-empty meta description, exactly one canonical URL, the expected entity graph, and a `<lastmod>` sourced from git (matching the visible stamp); the quality gate fails if any description is missing (spec US4 Independent Test; SC-003, SC-004, SC-006, SC-007).

### Tests for User Story 4 ⚠️

> Author FIRST; fails until the graph + sitemap land.

- [x] T013 [P] [US4] Author `docs-site/tests/seo-schema-org.spec.mjs` (Playwright, Chromium-only). Parse the `<script type="application/ld+json">` `@graph` and assert: Organization `@id` **equals** WebSite `publisher` `@id` (cross-reference invariant); a Person entity is present (`name == "Fredrick Gabelmann"`); and on the landing page the SoftwareApplication `offers.price == "0"`; and NO `FAQPage`/`HowTo` is emitted (D12, C2, FR-013/014/015/028, SC-006).
- [x] T014 [P] [US4] Author `docs-site/tests/seo-sitemap.spec.mjs` (Playwright, Chromium-only). Fetch `/sitemap-index.xml` (+ `sitemap-0.xml`) and assert each `<lastmod>` is a valid ISO-8601 date AND is **not** the build time (e.g. not "today" for unchanged pages), with `loc` values under `SITE_BASE` (D12, C7, FR-017/FR-012, SC-007/SC-010).

### Implementation for User Story 4

- [x] T020 [US4] Fill in the JSON-LD body in `docs-site/src/routeData.ts` (skeleton from T006): call `buildGraph` (T005) to append one `<script type="application/ld+json">` per route with Organization + WebSite site-wide (FR-013), SoftwareApplication ONLY when the route slug matches the `pluginPages` allowlist (landing page `index.mdx`, FR-014), and Person (FR-015). WebSite `publisher["@id"]` MUST equal Organization `@id` (C2 invariant). MUST NOT emit `FAQPage`/`HowTo` (FR-028). All `@id`/URLs from `site`+`base` (FR-013, DOC-012-flip-safe).
- [x] T021 [US4] Implement the sitemap `serialize()` in `docs-site/astro.config.mjs` (hook registered in T004). Resolve every page's `<lastmod>` from a **SINGLE BULK `git log` walk** built once before serialize runs (e.g. one `git log --name-only --pretty=%cI` / `--name-status` pass into a slug→date map) — NOT one `git log` subprocess per page (O(pages) is the documented slow path, withastro/astro#16803; Starlight's `lastUpdated` already bulk-walks). Apply a per-page frontmatter date override on top of the map (FR-017). No-history fallback (FR-017 edge): if a page has no commit entry, use its frontmatter date if pinned, otherwise leave `lastmod` **undefined** so `@astrojs/sitemap` OMITS the `<lastmod>` element — NEVER build/deploy time, and do NOT set the integration's top-level `lastmod` option. Confirm the `child_process` use is within the docs-site safe-aids guard's allowed surface (`validate-doc006-safe-aids.mjs`; plan implementation notes). (FR-017, C7, SC-007)
- [x] T022 [US4] Verify Starlight's built-in `lastUpdated: true` (enabled in T004) renders a visible "last updated" stamp from the git commit date that matches the sitemap `<lastmod>` (both from git), and follows the same no-history resolution order — frontmatter date if pinned, otherwise no stamp shown; the build-time value MUST NOT appear (FR-018, C8, SC-007). Rely on the Starlight built-in; do NOT add a parallel mechanism.
- [x] T023 [P] [US4] Author a non-empty, page-appropriate `description:` frontmatter line on each of the 12 hand-authored content pages: `docs-site/src/content/docs/index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`, `first-run.md`, `glossary.md`, `reference.md`, `security-and-trust.md`, `troubleshooting.md`, `update-and-rollback.md`, `contribute-and-release.md`, `install/claude-code.md`, `install/codex.md` (D9, FR-009). These are presence-satisfying; DOC-015 refreshes them (T034). Do NOT rewrite prose/voice (FR-025).
- [x] T024 [US4] In `docs-site/scripts/generate-reference-pages.mjs`, add a `description:` line to the `renderPage()` frontmatter block (~lines 671–675) so the 7 generated reference pages (`skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, `source-vs-dist`) emit a `description` in frontmatter — currently `renderPage()` emits it as body text, and `reference:generate` overwrites those files so hand-edits would be wiped (D9, FR-009). After the change, `pnpm --dir docs-site reference:check` (`--check`) MUST still pass.
- [x] T025 [US4] Add `validateMetaDescriptions(diagnostics)` to `docs-site/scripts/validate-docs-quality.mjs` (new function added to the `validateDocsQuality()` runner, ~line 506). It MUST glob `src/content/docs/**/*.{md,mdx}` and push a diagnostic (FAIL, non-zero) for any page with a missing or empty `description` frontmatter (D9, FR-010, C9, SC-003 — today 0/19). Canonical (C3) needs no code: rely SOLELY on Starlight's built-in `<link rel="canonical">` from `site`+`base`; add NO second source (FR-011, FR-027). Confirm `pnpm --dir docs-site validate:quality` passes once all 19 descriptions (T023 + T024) exist and fails if any is removed.

**Checkpoint**: Every page has a description (gate-enforced), one canonical, the entity graph, git-dated `<lastmod>` + matching visible stamp; `seo-schema-org.spec.mjs` and `seo-sitemap.spec.mjs` pass. US4 is independently testable.

---

## Phase 7: User Story 5 — Shared page renders a social card (Priority: P3)

**Goal**: Every content page references a per-page Open Graph card titled for that page (not one generic site-wide image), generated at build time via `astro-og-canvas`, with `og:image`/`twitter:image` tags injected by the shared route-data middleware (D5, C6).

**Independent Test**: Request `/og/<slug>.png` for a content page and confirm a card titled for that page is produced, and the page's `<head>` references it via `og:image`/`twitter:image` (spec US5 Independent Test; SC-008).

### Implementation for User Story 5

- [x] T028 [US5] Create the OG-card endpoint `docs-site/src/pages/og/[...slug].ts` using `astro-og-canvas`'s `OGImageRoute` with `export const prerender = true` and `getStaticPaths` over the content collection, rendering one PNG per content page titled/labelled for that page, using the `.ttf`/`.otf` face + PNG logo from T003 (D5, FR-019, FR-020, C6). No caching layer (build-time, ~19 pages — KISS/YAGNI; plan Performance Goals).
- [x] T029 [US5] Fold the per-page `og:image` and `twitter:image` meta tags into the SAME `docs-site/src/routeData.ts` middleware (skeleton T006, JSON-LD added T020) so every content page references its `/og/<slug>.png` card — reusing the one head-injection mechanism, not a second (D5 KISS, C6). The card is referenced only in `<head>` and is NOT a render-blocking or on-page-loaded asset (plan Performance Goals; FR-019).

**Checkpoint**: Each page references its per-page card; cards build under `dist`. US5 is independently testable.

---

## Phase 8: User Story 6 — Maintainer can verify the discoverability goal (Priority: P3)

**Goal**: Ship a documentation artifact that defines "AI-discoverable" as an observable measure and names the measurement source(s), with NO numeric target (D11, C11).

**Independent Test**: Read the success-metric doc and confirm it defines "AI-discoverable" as a concrete observable measure, names the measurement sources, and asserts no numeric target (spec US6 Independent Test; SC-009).

### Implementation for User Story 6

- [x] T030 [US6] Create `docs/ai/specs/doc-014-ai-discoverability-success-metric.md` defining "AI-discoverable" as an observable measure (FR-021), naming the measurement sources — **Google Search Console "Generative AI" performance reports** + a **GA4 AI-referrer channel group** (chatgpt.com / perplexity.ai / claude.ai / gemini) (FR-022) — and asserting NO numeric target (the site is not indexed until launch; target deferred to a post-launch baseline, FR-023, SC-009). This is also the artifact that records the FR-005 allow-training divergence (T016). It MUST ALSO carry the **FR-016 justification**: state that the JSON-LD structured data is a classic-search rich-results + entity-disambiguation mechanism, and explicitly NOT an answer-engine/LLM citation lever (LLMs strip JSON-LD and read visible HTML). Note DOC-018 owns analytics activation. (C11, FR-016, C2)

**Checkpoint**: The success-metric definition exists and is verifiable by reading it. US6 is complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: CI/config wiring that makes the new surfaces actually run and deploy correctly, plus the cross-spec coordination note and the PR review packet.

- [x] T031 Broaden `docs-site/playwright.config.mjs` `testMatch` from the single-file `'docs-smoke.spec.mjs'` to a glob (e.g. `'**/*.spec.mjs'`) so the four new SEO specs (T010, T013, T014, T017) actually run — otherwise they never execute (plan implementation notes; D12).
- [x] T032 Set `fetch-depth: 0` on the `actions/checkout` step in `.github/workflows/deploy-docs.yml`. The current shallow (depth-1) clone would collapse every page's git date to the single deploy commit, breaking SC-007 in CI even though it passes on a local full clone (D8, FR-017). The PR description must confirm CLAUDE.md's CI/CD sections need NO update — this is a checkout-depth change, not a job rename / permission / required-check-name change (D8, plan CI note).
- [x] T035 Confirm the regenerated `docs-site/pnpm-lock.yaml` (from T002) is staged for commit, since CI installs with `--frozen-lockfile` (`deploy-docs.yml`) — a stale lockfile fails the deploy job (plan implementation notes; research "Cross-cutting facts"). Lockfile churn is a generated artifact excluded from the production-file count.
- [x] T034 Record a "refresh meta descriptions" follow-up into DOC-015's scope (the editorial feature): the 12 + 7 descriptions authored now (T023, T024) are presence-satisfying only; DOC-015's prose pass deliberately revisits them. Add the coordination note to the DOC-015 roadmap entry / scope (D9, spec Assumptions "Coordination with the editorial feature", FR-025 deferral). This is a cross-spec note, not a prose rewrite here.
- [x] T026 Run `pnpm --dir docs-site validate` (reference check, `astro check`, build/links, safe-aids, quality gate including `validateMetaDescriptions`, Playwright smoke + the 4 new SEO specs) and confirm it is green. This also proves the "no generated surface degrades silently" posture: any generation failure (OG card, per-page `.md`, digest, sitemap, JSON-LD) fails the `astro build` step loudly inside `validate` (spec Edge Cases; plan build-failure posture).
- [x] T027 Run the `quickstart.md` per-surface validation runbook and confirm each contract (C1–C11) check passes against the built site.
- [x] T033 Generate/update the PR review packet per the spec's "PR Review Packet Requirements": what changed + why; non-goals (the FR-024…FR-029 boundaries — no training block (FR-024), no prose rewrite (FR-025), no analytics/404-legal/domain-flip (FR-026), no `astro-seo`/second canonical (FR-027), no FAQ/HowTo or content negotiation (FR-028), noindex guard preserved (FR-029), no numeric target (FR-023)); review order (1: robots.txt + `public/robots.txt` removal + quality-gate retarget; 2: `routeData.ts` + `lib/schema.ts`; 3: `[...slug].md.ts` + `astro.config.mjs`; 4: OG route + assets; 5: descriptions + generator + `validateMetaDescriptions`; 6: success-metric doc + `deploy-docs.yml`); scope budget; per-FR-group traceability → files → verification (C1–C11, data-model); verification evidence (`pnpm --dir docs-site validate` + the SEO specs); known gaps + owning features (meta-description refresh → DOC-015; analytics + launch hygiene → DOC-018; domain flip + noindex removal → DOC-012; numeric target → post-launch); rollback notes (additive; noindex guard stays, so rollback = removal of added policy/metadata without changing indexing posture). (plan PR review packet source)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T002 depends on T001 (deps must be declared before install).
- **Foundational (Phase 2)**: Depends on Setup (the integrations/plugins must resolve). BLOCKS endpoint behavior in all user stories. T004 (astro.config wiring) must precede the endpoints it registers.
- **User Stories (Phase 3–8)**: All depend on Foundational completion. Then:
  - US1 (P1) and US4 (P1) are the launch-blocking MVP baselines.
  - US2 (P2) extends US1's `robots.txt.ts` (T015 depends on T011).
  - US3 (P2), US5 (P3), US6 (P3) are independent of each other given the foundation.
- **Polish (Phase 9)**: Depends on the user stories whose output it validates/wires (T031 needs the test specs; T026/T027 need all surfaces; T032/T035 are CI wiring).

### Critical cross-task dependencies (within/between stories)

- **T011 → T015**: US2 extends the same `robots.txt.ts` file US1 creates (sequential, same file).
- **T012 ↔ T012a**: deleting `public/robots.txt` (T012) and retargeting the quality gate's robots assertion (T012a) are coupled — the gate must assert the endpoint policy, not the deleted static file, or `validate:quality` fails.
- **T006 → T020 → T029**: `routeData.ts` is the SHARED head-injection mechanism — skeleton (T006, foundational), JSON-LD body (T020, US4), OG tags (T029, US5). These touch the same file and MUST be sequential, not parallel.
- **T005 → T020**: `schema.ts` factories must exist before the middleware calls `buildGraph`.
- **T004 → T021**: the sitemap `serialize` hook is registered in `astro.config.mjs` (T004); its body lands in T021.
- **T003 → T028**: OG assets must exist before the OG route renders cards.
- **T023 + T024 → T025**: all 19 descriptions must exist before the presence gate can pass.
- **T030 → T016**: the success-metric doc (T030) is where the allow-training divergence (T016) is recorded.
- **T031 → T026**: `testMatch` must be broadened before `validate` runs the new specs.

### Within Each User Story

- Tests (T010, T013, T014, T017) are authored before/with the behavior they verify (TDD) and FAIL until implementation lands.
- Shared modules (schema, middleware) before the endpoints that consume them.
- Story complete before moving to the next priority.

### Parallel Opportunities

- **Setup**: T003 [P] (OG assets) is independent of T001/T002.
- **Foundational**: T005 [P] (`schema.ts`) and T006 [P] (`routeData.ts` skeleton) are different files, parallel-safe after T004.
- **Tests**: T010, T013, T014, T017 are different files — all [P], authorable together up front.
- **US4 content**: T023 [P] (the 12 description edits) is independent of the structured-data/sitemap code (T020/T021). Each of the 12 content files is itself parallel-safe.
- **Cross-story**: once the foundation is done, US3 (T017–T019), US5 (T028–T029), and US6 (T030) can proceed in parallel with US4 — EXCEPT T029 (US5 OG tags) shares `routeData.ts` with T020 (US4 JSON-LD), so those two serialize.

---

## Parallel Example: Author all e2e specs up front (TDD)

```bash
# All four SEO specs are different files — author them together, watch them fail,
# then make them pass as each surface lands:
Task: "Author docs-site/tests/seo-robots-txt.spec.mjs (training ALLOWED, citation ALLOWED, default allowed, Sitemap present)"   # T010
Task: "Author docs-site/tests/seo-schema-org.spec.mjs (Org @id == WebSite publisher @id; SWApp price 0; Person present)"        # T013
Task: "Author docs-site/tests/seo-sitemap.spec.mjs (<lastmod> valid ISO from git, not build time)"                              # T014
Task: "Author docs-site/tests/seo-llms-txt.spec.mjs (3 digests 200 + non-empty)"                                                # T017
```

## Parallel Example: User Story 4 description authoring

```bash
# The 12 hand-authored description edits are independent files (T023):
Task: "Add description: to docs-site/src/content/docs/index.mdx"
Task: "Add description: to docs-site/src/content/docs/first-run.md"
Task: "Add description: to docs-site/src/content/docs/glossary.md"
# ... (9 more, one per hand-authored page)
```

---

## Implementation Strategy

### MVP First (the two P1 stories)

The launch-blocking baseline is **US1 (citation crawler access) + US4 (correct metadata)** — both P1. Suggested MVP:

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004, T005, T006, T009A).
3. Complete Phase 3 (US1) and Phase 6 (US4).
4. **STOP and VALIDATE**: `/robots.txt` allows the citation tier + advertises the sitemap; every page has a description (gate-enforced), one canonical, the entity graph, and a git-dated `<lastmod>` + visible stamp.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 (citation access) + US4 (metadata) → P1 baseline (MVP).
3. US2 (training-tier allow) → max-discoverability posture (extends US1's file).
4. US3 (agent retrieval: digests + per-page `.md`) → coding-agent surface.
5. US5 (per-page OG cards) → share-quality.
6. US6 (success-metric doc) → verifiable goal.
7. Polish: broaden `testMatch`, `fetch-depth: 0`, commit lockfile, DOC-015 coordination note, run `validate` + quickstart, PR packet.

### Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- The single shared-config + shared-head-middleware surface (`astro.config.mjs`, `routeData.ts`) is why this is one atomic slice; the A/B split is the documented PR-emission fallback ONLY if the post-Tasks atomicity classifier recommends it (T009A).
- Build outputs (cards, digests, per-page `.md`, sitemap, JSON-LD) all fail the build loudly on generation error — no silent degradation (spec Edge Cases).
- Negative requirements are hard boundaries: no training block (FR-024), no `astro-seo` / second canonical (FR-027), no production-domain hardcode (FR-012), no numeric metric target (FR-023), no prose rewrite (FR-025), noindex guard preserved (FR-029).
