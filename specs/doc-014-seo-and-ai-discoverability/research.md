# Phase 0 Research: SEO and AI Discoverability (DOC-014)

**Feature**: `doc-014-seo-and-ai-discoverability`
**Date**: 2026-06-25
**Input**: `spec.md` + resolved Clarify decisions + `docs/ai/specs/.process/DOC-014-design-concept.md`

All open decisions were resolved during scaffold (grill-me) and the Clarify
consensus passes recorded in the Design Concept. This file consolidates each
decision in `Decision / Rationale / Alternatives considered` form, grounded in
(a) an inventory of the proven sibling site under
`../../../landing-page/website/` and (b) the cited 2026 SEO/GEO research carried
from the Design Concept. **No `[NEEDS CLARIFICATION]` markers remain.**

---

## D1 — Crawler-access policy: allow the AI-training tier (invert the sibling)

**Decision**: Ship a NEW dynamic endpoint `docs-site/src/pages/robots.txt.ts`
emitting a 3-tier policy:

1. **Training tier ALLOW** — `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`,
   `ClaudeBot` each get `Allow: /`. This **inverts** the sibling
   (`landing-page/website/src/pages/robots.txt.ts`), which `Disallow: /`s exactly
   these five.
2. **Citation tier ALLOW** — `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`,
   `Claude-User`, `PerplexityBot`, `Perplexity-User` each get `Allow: /`.
3. **Default `*` ALLOW**, then a `Sitemap:` line whose absolute URL is derived
   from `site` + `base` (NOT `astro:env` — verified that no `astro:env` schema is
   configured in this docs-site).

`docs-site/public/robots.txt` (currently `User-agent: *\nDisallow: /`) **is
deleted** because a static `public/robots.txt` shadows the endpoint at the same
route.

**Rationale**: Training and citation crawlers are *separate* user-agents
(OpenAI/Anthropic/Cloudflare bot docs, 2025-26): `GPTBot` is training-only,
`OAI-SearchBot` is search/citation-only, and blocking `Google-Extended` does not
remove a site from AI Overviews. So blocking training buys nothing for citation,
while allowing it plausibly gets a free OSS dev-tool into base-model
recommendations (FR-002, FR-024). The citation tier (FR-001) is allowed either
way. Deriving the sitemap URL from `site`+`base` keeps the policy
DOC-012-flip-safe (FR-004, FR-012): when DOC-012 changes the single `site` value
at launch, the advertised sitemap URL finalizes automatically.

**Alternatives considered**:
- *Block the training tier (match sibling)*: protective default; forgoes
  base-model presence at no citation benefit — rejected per the deliberate
  max-discoverability posture (FR-024).
- *Granular allow/block per bot*: harder to justify and maintain; rejected on
  KISS grounds.
- *Use `astro:env` `PUBLIC_SITE_URL` like the sibling*: rejected — no
  `astro:env` schema is configured here; introducing one is unnecessary
  ceremony (YAGNI) when `site`+`base` are already authoritative.

**Sibling divergence note (FR-005)**: the allow-training decision is recorded in
the success-metric documentation artifact so a future maintainer does not "fix"
it back to a blocking default.

---

## D2 — Structured data: route-data middleware + ported schema factory

**Decision**: Emit a JSON-LD `@graph` via a Starlight **route-data middleware**
`docs-site/src/routeData.ts` (registered with Starlight's `routeMiddleware`
config option), backed by ported factory functions in `docs-site/src/lib/schema.ts`.
Entities:

- **Organization** (`@id` = `<site>#organization`, `name` "Racecraft Lab",
  `sameAs` = `["https://github.com/racecraft-lab"]`) and **WebSite**
  (`@id` = `<site>#website`, `publisher` → Organization `@id`) on **every route**.
- **SoftwareApplication** (`offers.price` `0`) **only** on the landing page
  `src/content/docs/index.mdx`, gated by an explicit `pluginPages` allowlist map
  (slug → application metadata).
- **Person** (`name` "Fredrick Gabelmann", `sameAs` =
  `["https://github.com/fgabelmannjr"]`, `worksFor` → Organization `@id`,
  `@id` = `<site>#person`).

All `@id` values and URLs are derived from `site` + `base` (DOC-012-flip-safe).

**Rationale**: The sibling's schema *factory functions* (`buildOrganizationSchema`,
`buildWebSiteSchema`, `buildPersonSchema`, `buildGraph`) port in substance; only
the injection mechanism differs on Starlight. Starlight 0.40 docs call a
`Head.astro` component override **"a last resort"** and recommend **route
middleware** (added in v0.32) for augmenting page `<head>`. Route middleware runs
for every route and can append a JSON-LD `<script>` tag to the page's head
entries, satisfying the "site-wide Organization + WebSite" requirement (FR-013)
without per-page authoring. The `SoftwareApplication` `offers.price: 0` is the
most on-point free/OSS rich result and is still live in 2026 (FR-014). The Person
entity supports author/contributor disambiguation / E-E-A-T (FR-015).

**Deliberate value changes from the sibling factory**:
- `sameAs` retargets to the `racecraft-lab` GitHub org (sibling used
  `fgabelmannjr/racecraft`).
- Person `@id` becomes `<site>#person` (sibling used `#founder`); **no PII** is
  placed in the `@id` fragment, and the email `contactPoint` block is dropped.
- `FAQPage` and `HowTo` factories are **not ported** — FAQ rich results retired
  May 2026, HowTo desktop retired 2023 (FR-028 sunset).
- The sibling's `SearchAction.potentialAction` on WebSite is **not required** by
  any FR and is omitted unless trivially portable (kept minimal per KISS).

**Justification framing (FR-016)**: the feature documentation justifies JSON-LD
strictly as a **classic-search rich-results + entity-disambiguation** mechanism
and explicitly does **not** claim it as an answer-engine citation lever (LLMs
strip JSON-LD and read visible HTML).

**Alternatives considered**:
- *`Head.astro` component override* (sibling's layout-injection analogue):
  rejected — Starlight 0.40 designates it a last resort vs. route middleware.
- *Global `head:` array in `astro.config.mjs`*: works for a *static* graph but
  cannot vary per-route (SoftwareApplication only on the landing page), so route
  middleware is required anyway; keeping all JSON-LD in one mechanism is simpler
  than splitting static + per-page.
- *Add `schema-dts` typing dependency (sibling uses it)*: rejected — the factory
  substance ports without it; adding a types-only dep is unnecessary for ~4 small
  builders (YAGNI). Plain typed object literals suffice.

---

## D3 — Per-page agent-readable Markdown: dependency-free custom endpoint

**Decision**: Serve the per-page text variant from a custom Astro endpoint
`docs-site/src/pages/[...slug].md.ts` that reads `getCollection('docs')` and
returns each page's raw `body` as `text/markdown`, with
`export const prerender = true`. **No plugin.**

**Rationale** (Clarify S1 consensus, 2/2 high-confidence): This product's docs
ARE consumed by coding agents (Claude Code/Codex), so per-page `.md` is squarely
on-target (US3, FR-007). `astro-markdown-for-agents` does not exist as a current
package; `starlight-dot-md` (3★, Starlight 0.40 compat unverified) and
`starlight-md-txt` (`.md.txt` URL, unverifiable) both lose to a ~15-line
dependency-free endpoint that composes trivially (the links-validator validates
HTML only; `starlight-llms-txt` emits only `.txt`). Iterating `getCollection('docs')`
guarantees one variant per content page with no orphans (FR-008). Distinct
build-time URLs are used because Astro static cannot honor `Accept: text/markdown`
content negotiation, and no crawler honors it for a static site anyway (FR-028,
spec Edge Cases).

**Known acceptable behavior (FR-007)**: the 3 MDX content pages
(`index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`) emit their raw
`body`, which includes `import` statements and JSX. This is acceptable per FR-007
(the variant returns source `body`, not rendered prose).

**Alternatives considered**:
- *`starlight-dot-md` / `starlight-md-txt` plugins*: rejected on
  KISS/verifiability — unverified 0.40 compatibility and a non-standard `.md.txt`
  URL; a tiny endpoint is simpler and FR-008-guaranteed.
- *llms.txt tiers only (no per-page)*: rejected — bulk `llms-full.txt` does not
  serve targeted single-page retrieval (US3 AS2).

---

## D4 — Whole-site digest: `starlight-llms-txt`

**Decision**: Add `starlight-llms-txt` v0.10.0 as a Starlight `plugins:` entry.
It emits `llms.txt`, `llms-full.txt`, and `llms-small.txt`.

**Rationale**: Purpose-built for Starlight by the Astro-docs maintainer (delucis);
generates the three digest tiers against Starlight's own content model with no
DOM-selector retuning and no Tailwind jsdom patch (FR-006, US3 AS1). The sibling's
`@4hse/astro-llms-txt` assumes the landing-page DOM (custom
`mainSelector`/`ignoreSelectors` + a Tailwind patch) and would need rework for a
docs site with no upside.

**Alternatives considered**:
- *Port the sibling's `@4hse/astro-llms-txt`* (roadmap's literal wording):
  rejected — strictly more porting work; the intent (ship llms.txt tiers as a
  coding-agent retrieval aid) is preserved by the Starlight-native plugin.

---

## D5 — Open Graph: per-page dynamic cards via `astro-og-canvas`

**Decision**: Add `astro-og-canvas` v0.11.1 (and its `canvaskit-wasm` peer/dep).
Generate cards from an `OGImageRoute` endpoint
`docs-site/src/pages/og/[...slug].ts` with `export const prerender = true`, and
inject `og:image` / `twitter:image` per-page via the **same** `src/routeData.ts`
middleware that emits JSON-LD.

**Rationale**: Per-page titled cards improve share quality when individual doc
pages are posted (US5, FR-019, FR-020). Build-time generation keeps the static
output model intact. Reusing the route-data middleware for the per-page
`og:image`/`twitter:image` tags avoids a second head-injection mechanism (KISS).

**Build-only assets (excluded from reviewable LOC)**: `astro-og-canvas` renders
through CanvasKit/Skia, which requires a `.ttf`/`.otf` display face and a **PNG**
logo — `woff2` and `SVG` do **not** load in CanvasKit. These go under
`docs-site/src/assets/og/` and are generated/binary build inputs, not
hand-reviewed source (consistent with the spec's Reviewability Notes excluding
generated card images).

**Alternatives considered**:
- *Single static branded OG card* (grill-me's budget-minimal recommendation):
  user chose per-page dynamic; this is the main swing factor in the LOC estimate.
- *`starlight-og` plugin*: equivalent build-time approach; `astro-og-canvas` +
  `OGImageRoute` is selected because it integrates cleanly with the existing
  `passthroughImageService` config and gives explicit control over the per-page
  route and asset inputs.

---

## D6 — Sitemap: promote `@astrojs/sitemap`, git-dated `<lastmod>`

**Decision**: Promote `@astrojs/sitemap` (3.7.3, currently transitive via
Starlight) to a **direct dependency** and add it to the Astro `integrations`
array with a custom `serialize()` that sources each page's `<lastmod>` from its
git commit date (`git log -1 --pretty=%cI <file>`), honoring a per-page
frontmatter date override (FR-017).

**Rationale**: Google trusts `lastmod` only when "verifiably accurate" against
real changes (Google Search Central, 2026) — the git commit date is exactly that,
never build time. Starlight 0.40 **defers** to a user-provided `@astrojs/sitemap`
(verified guard at `@astrojs/starlight` `index.ts:107-109`), so adding the
integration directly does **not** raise a duplicate-instance error. The default
`@astrojs/sitemap` `<lastmod>` is build time, which Google distrusts — the custom
`serialize()` corrects this (the sibling currently inherits the build-time
default).

**Alternatives considered**:
- *Frontmatter `lastUpdated` only*: controlled but goes stale silently — rejected
  as the sole source; kept only as an explicit per-page override.
- *Keep the build-time `@astrojs/sitemap` default*: Google distrusts it; the
  roadmap rules it out.

---

## D7 — Visible "Last updated" stamp: Starlight `lastUpdated: true`

**Decision**: Enable Starlight's built-in `lastUpdated: true` (with frontmatter
override allowed). This is wired **separately** from the sitemap (D6), though both
draw from the same git history.

**Rationale**: Starlight's `lastUpdated` reads the git commit date and renders a
visible stamp for free (FR-018), consistent with the sitemap `<lastmod>` so the
visible date matches the freshness signal (SC-007).

---

## D8 — Deploy CI: full git history for accurate dates

**Decision**: Set `fetch-depth: 0` on the `actions/checkout` step in
`.github/workflows/deploy-docs.yml`.

**Rationale**: The current checkout is a shallow (depth-1) clone, so
`git log -1 --pretty=%cI <file>` and Starlight `lastUpdated` would both collapse
every page's date to the single deploy commit — SC-007 ("none report the build
time") fails in CI even though it passes locally on a full clone.
`fetch-depth: 0` fetches full history so per-file commit dates resolve correctly.

**CLAUDE.md note**: this edits a CI workflow (`deploy-docs.yml`). Per the repo
convention, the implementing PR description must confirm whether CLAUDE.md's
CI/CD sections need updates (they do not — this is a checkout-depth change, not a
job/permission/check-name change).

---

## D9 — Meta descriptions: author 12, generate 7, enforce presence

**Decision**:
- Author `description:` frontmatter on the **12 hand-authored** content pages.
- For the **7 generated** reference pages (`PAGE_SLUGS = skills, agents,
  manifests, hooks, scripts, tests, source-vs-dist`), emit `description:` from
  inside `docs-site/scripts/generate-reference-pages.mjs` (the `renderPage()`
  frontmatter block), because `reference:generate` overwrites those files and
  would wipe any hand-edit.
- Add a `validateMetaDescriptions(diagnostics)` function to
  `docs-site/scripts/validate-docs-quality.mjs` that globs
  `src/content/docs/**/*.{md,mdx}` and **fails** on any missing/empty
  `description`.

**Rationale**: DOC-014 is the SEO/metadata spec, so shipping descriptions is its
job (FR-009), and the presence-requiring validator only passes if they exist
(FR-010, SC-003 — today 0/19). Verified: the `page()` factory in
`generate-reference-pages.mjs` already carries a `description` field, but
`renderPage()` currently emits it as **body text**, not frontmatter — the change
is a surgical addition of one `description:` line to the frontmatter block. The
roadmap's "author after prose so they don't go stale" note is honored by an
explicit "refresh meta descriptions" task added to DOC-015's scope (coordination
note, FR-025 deferral).

**Alternatives considered**:
- *Defer authoring to DOC-015, rule warn-only now*: rejected — warn-only rules
  are easy to ignore and split one concern across two specs.

---

## D10 — Canonical: rely solely on Starlight's built-in

**Decision**: Rely **solely** on Starlight's built-in `<link rel="canonical">`
(emitted from `site` + `base`). Do **not** add `astro-seo`.

**Rationale**: Starlight auto-emits exactly one canonical from `site`+`base`, so
canonical + sitemap URLs finalize automatically at the DOC-012 launch flip
(FR-011, FR-012, SC-004, SC-010). Adding `astro-seo` would **double-emit**
canonical (FR-027 forbids a second canonical source).

**Alternatives considered**:
- *Add `astro-seo`*: rejected — duplicate canonical risk (FR-027).
- *Hardcode the production domain now*: rejected — advertises 404 URLs on the
  noindex'd staging site (spec Edge Cases, FR-012).

---

## D11 — Success metric: observable definition + measurement source, no target

**Decision**: Ship a documentation artifact (under `docs/ai/specs/`) that defines
"AI-discoverable" as an **observable measure** and names the measurement sources:
**Google Search Console "Generative AI" performance reports** + a **GA4
AI-referrer channel group** (chatgpt.com / perplexity.ai / claude.ai / gemini).
**No numeric target** is asserted.

**Rationale**: A goal with no written definition and no measurement source cannot
be verified (US6, FR-021, FR-022, SC-009). No numeric target — the site is not
indexed until launch, so any threshold would be invented (FR-023, SC-009). This
artifact also records the FR-005 allow-training divergence so the posture is not
"fixed" back later. DOC-018 owns analytics activation; targets come post-launch
with a real baseline.

**Alternatives considered**:
- *Define + set an initial numeric target*: rejected — zero baseline makes the
  number a guess (FR-023).
- *Defer the metric entirely to DOC-018*: rejected — leaves DOC-014's own
  headline goal unverifiable.

---

## D12 — Tests: port sibling e2e patterns into `docs-site/tests/` (Chromium-only)

**Decision**: Port the sibling's e2e assertion patterns into `docs-site/tests/`
(Playwright, Chromium-only, matching the existing `docs-smoke.spec.mjs` style):

- **robots-txt**: assert the training tier is **ALLOWED** (the inverse of the
  sibling's "blocked" assertion), the citation tier is allowed, default `*` is
  allowed, and a `Sitemap:` directive is present.
- **schema-org**: Organization `@id` **equals** WebSite `publisher` `@id`;
  SoftwareApplication `offers.price` is `0` on the landing page; a Person entity
  is present.
- **llms-txt**: the three digest files (`llms.txt`, `llms-full.txt`,
  `llms-small.txt`) each return 200 and are non-empty.
- **sitemap**: each `<lastmod>` is a valid ISO date sourced from git, not build
  time.

**Rationale**: These deterministic checks back SC-001/002 (crawler allows),
SC-005 (digests + per-page variants fetchable), SC-006 (entity graph present),
and SC-007 (git-dated lastmod). Chromium-only mirrors the existing smoke suite
and the sibling's `test.skip(browserName !== 'chromium')` guard.

**Integration with the existing harness**:
- `playwright.config.mjs` currently pins `testMatch: 'docs-smoke.spec.mjs'`
  (single file). New spec files in `docs-site/tests/` will **not** run until
  `testMatch` is broadened to a glob (e.g. `**/*.spec.mjs`) — this is a required,
  surgical config edit recorded in the plan.
- The Playwright `webServer` serves the built site at `…/racecraft-plugins-public/`,
  so the new endpoints (`robots.txt`, `og/*`, `*.md`, `sitemap-index.xml`, the
  llms.txt tiers) are fetchable via `request.get(...)` exactly as the sibling
  fetches `/robots.txt`.

**Alternatives considered**:
- *Assert in `validate-docs-quality.mjs` only*: the quality gate already enforces
  description presence (D9) and the robots policy shape (D1 retarget), but
  rendered-output assertions (JSON-LD graph, OG tags, llms.txt bodies) need a
  built site — Playwright against the preview server is the right layer.

---

## Cross-cutting facts verified against the live tree

- **`node_modules` is ABSENT** in the doc-014 worktree's `docs-site/` — the
  Implement phase must run `pnpm --dir docs-site install` after adding deps.
- **`docs-site/pnpm-lock.yaml` exists** and CI installs with
  `--frozen-lockfile` (`deploy-docs.yml`), so the lockfile must be regenerated
  and committed when the new deps are added — otherwise the deploy job fails.
- **`validate-docs-quality.mjs`** constants: `DOC011_STAGING_ROBOTS_PATH`
  (line 69) and the `validateStagingIndexingGuard()` robots assertion (lines
  423-430) are what D1 retargets; the **noindex-meta assertion** (lines 432-438)
  is the real indexing guard (FR-029) and is **kept intact**.
- **`astro.config.mjs`** keeps `site: 'https://racecraft-lab.github.io'`,
  `base: '/racecraft-plugins-public'`, `passthroughImageService()`, and the
  DOC-011 `noindex, nofollow` head meta — all untouched except the additive
  `integrations`/`plugins`/`lastUpdated` wiring (FR-029, spec Edge Cases).
- **Content inventory**: 19 content pages = 12 hand-authored + 7 generated;
  0 currently carry a `description` (SC-003 baseline confirmed).
