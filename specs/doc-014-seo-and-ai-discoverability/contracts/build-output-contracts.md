# Build-Output Contracts: SEO and AI Discoverability (DOC-014)

**Feature**: `doc-014-seo-and-ai-discoverability`
**Date**: 2026-06-25

This static site exposes its "interfaces" as build-time URLs and rendered
metadata that crawlers, answer engines, and coding agents consume. Each contract
below states the route/output, what it MUST contain, and the verification layer
(Playwright e2e under `docs-site/tests/`, or the `validate-docs-quality.mjs`
quality gate). All absolute URLs derive from `site` + `base`
(`SITE_BASE = https://racecraft-lab.github.io/racecraft-plugins-public` on
staging; flips with DOC-012).

---

## C1 — `GET /robots.txt` (crawler-access policy)

**Producer**: `docs-site/src/pages/robots.txt.ts`
**Content-Type**: `text/plain; charset=utf-8` — **Status**: `200`

MUST contain, in order:

1. Training tier, each with `Allow: /`:
   `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot`.
2. Citation tier, each with `Allow: /`:
   `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`,
   `PerplexityBot`, `Perplexity-User`.
3. `User-agent: *` with `Allow: /`.
4. `Sitemap: ${SITE_BASE}/sitemap-index.xml`.

MUST NOT contain `Disallow: /` for any training-tier user-agent (this is the
inverse of the sibling). The static `docs-site/public/robots.txt` MUST be absent
(removed) so it cannot shadow this route.

**Verifies**: FR-001, FR-002, FR-003, FR-004, FR-024 · SC-001, SC-002
**Verification**: e2e `docs-site/tests/seo-robots-txt.spec.mjs` (training ALLOW,
citation ALLOW, default ALLOW, Sitemap present) + quality-gate retarget of
`validateStagingIndexingGuard()`.

---

## C2 — JSON-LD `@graph` (structured data, every page)

**Producer**: `docs-site/src/routeData.ts` + `docs-site/src/lib/schema.ts`
**Form**: one `<script type="application/ld+json">` whose JSON has
`@context: "https://schema.org"` and an `@graph` array.

Every content page MUST include:
- **Organization** with `@id == ${SITE_BASE}#organization`, non-empty `name`
  ("Racecraft Lab"), `url`, `logo`, `sameAs` containing
  `https://github.com/racecraft-lab`.
- **WebSite** with `@id == ${SITE_BASE}#website` and
  `publisher["@id"] == Organization["@id"]` (cross-reference invariant).
- **Person** with `name == "Fredrick Gabelmann"`, `@id == ${SITE_BASE}#person`
  (no PII in the fragment), `worksFor["@id"] == Organization["@id"]`, `sameAs`
  containing `https://github.com/fgabelmannjr`.

The **landing page only** additionally includes:
- **SoftwareApplication** with `offers.price == "0"` (free/OSS).

MUST NOT emit `FAQPage` or `HowTo` (FR-028 sunset).

**Verifies**: FR-013, FR-014, FR-015, FR-016, FR-028 · SC-006
**Verification**: e2e `docs-site/tests/seo-schema-org.spec.mjs` — assert
Organization `@id` equals WebSite `publisher` `@id`; SoftwareApplication
`offers.price` is `"0"` on the landing page; a Person entity is present.

---

## C3 — Canonical link (every page, exactly one)

**Producer**: Starlight built-in (from `site`+`base`). **No** second source.

Every page MUST carry exactly one `<link rel="canonical">` resolving under
`SITE_BASE`. The feature MUST NOT add `astro-seo` or any parallel canonical
emitter (no duplicates).

**Verifies**: FR-011, FR-012, FR-027 · SC-004, SC-010
**Verification**: covered by Starlight's built-in behavior; the no-second-source
guarantee is structural (no `astro-seo` dependency added — visible in
`package.json`).

---

## C4 — Per-page Markdown variant `GET /<slug>.md`

**Producer**: `docs-site/src/pages/[...slug].md.ts` (`prerender = true`)
**Content-Type**: `text/markdown`

For every entry in `getCollection('docs')`, a `.md` URL MUST return that page's
raw `body`. There MUST be no orphaned variant (a `.md` with no rendered page) and
no content page missing a variant (one-to-one with the collection).

**Verifies**: FR-007, FR-008 · SC-005
**Verification**: derived from `getCollection('docs')` (one-to-one by
construction); spot-checked via the build and (optionally) an e2e fetch.

---

## C5 — Whole-site digests `GET /llms.txt`, `/llms-full.txt`, `/llms-small.txt`

**Producer**: `starlight-llms-txt` plugin.

Each of the three URLs MUST return HTTP 200 with a non-empty plain-text body
generated from site content.

**Verifies**: FR-006 · SC-005
**Verification**: e2e `docs-site/tests/seo-llms-txt.spec.mjs` — all three return
200 and non-empty bodies.

---

## C6 — Per-page Open Graph card `GET /og/<slug>.png` + head tags

**Producer**: `docs-site/src/pages/og/[...slug].ts` (`OGImageRoute`,
`prerender = true`); head injection via `docs-site/src/routeData.ts`.

Every content page MUST reference a per-page card image via `og:image` and
`twitter:image` meta tags, and the card MUST be titled/labelled for that page
(not a single site-wide generic image).

**Verifies**: FR-019, FR-020 · SC-008
**Verification**: build produces one card per page; head tags injected by the
shared route-data middleware.

---

## C7 — Sitemap `GET /sitemap-index.xml` (+ `sitemap-0.xml`)

**Producer**: `@astrojs/sitemap` (direct dep) with a custom `serialize()`.

Every page entry's `<lastmod>` MUST be a valid ISO-8601 date sourced from the
page's git commit date, resolved via a SINGLE BULK `git log` walk into a
slug→date map built once (NOT a per-file `git log` subprocess — the O(pages)
slow path, withastro/astro#16803), with a per-page frontmatter date override
honored. For a page with no commit history, `<lastmod>` is the frontmatter date
if pinned, else OMITTED. `<lastmod>` MUST NOT be the build time. `loc`
values derive from `site`+`base`.

**Verifies**: FR-017, FR-012 · SC-007, SC-010
**Verification**: e2e `docs-site/tests/seo-sitemap.spec.mjs` — `<lastmod>` is a
valid ISO date and is not the build time.

---

## C8 — Visible "Last updated" stamp

**Producer**: Starlight `lastUpdated: true` (frontmatter override allowed).

Every content page MUST render a visible "last updated" date consistent with the
sitemap `<lastmod>` (both from git commit date).

**Verifies**: FR-018 · SC-007
**Verification**: Starlight built-in render; consistency with C7 is structural
(same git source).

---

## C9 — Meta-description presence quality gate

**Producer**: `validateMetaDescriptions(diagnostics)` added to
`docs-site/scripts/validate-docs-quality.mjs`; run via `pnpm validate:quality`
(part of `pnpm validate`).

The gate MUST glob `src/content/docs/**/*.{md,mdx}` and FAIL (non-zero
diagnostics) when any page has a missing or empty `description` frontmatter.

**Verifies**: FR-009, FR-010 · SC-003
**Verification**: `pnpm --dir docs-site validate:quality` exits non-zero if any
description is missing; passes when all 19 are present.

---

## C10 — Staging indexing guard preserved (negative contract)

**Producer**: existing `astro.config.mjs` head meta (`noindex, nofollow`) +
`validateStagingIndexingGuard()` noindex assertion.

The DOC-011 `noindex, nofollow` head meta MUST remain. The
`validateStagingIndexingGuard()` **noindex-meta** assertion MUST stay intact; only
its **robots.txt** assertion is retargeted (from "static `public/robots.txt` ==
`Disallow: /`" to "the 3-tier endpoint policy"). No metadata/policy change weakens
indexing posture.

**Verifies**: FR-029 · spec Edge Cases (staging noindex still in force)
**Verification**: `pnpm --dir docs-site validate:quality` still asserts the
noindex meta; the robots assertion now asserts the endpoint policy.

---

## C11 — Success-metric documentation (negative-target contract)

**Producer**: a Markdown artifact under `docs/ai/specs/`.

MUST define "AI-discoverable" as an observable measure, MUST name the measurement
sources (GSC Generative AI reports + GA4 AI-referrer channel group), MUST record
the FR-005 allow-training divergence, and MUST NOT assert a numeric target.

**Verifies**: FR-005, FR-021, FR-022, FR-023 · SC-009
**Verification**: documentation review (read the artifact).
