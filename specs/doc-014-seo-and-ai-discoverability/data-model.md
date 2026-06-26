# Phase 1 Data Model: SEO and AI Discoverability (DOC-014)

**Feature**: `doc-014-seo-and-ai-discoverability`
**Date**: 2026-06-25

This feature has no database and no runtime persistence. The "entities" here are
**build-time data shapes** emitted into the static site: structured-data objects,
the crawler-access policy text, the agent-readable digests/variants, sitemap
entries, and the documented success-metric definition. All URLs and `@id` values
derive from the configured `site` + `base` so they finalize automatically at the
DOC-012 launch flip.

Shared derivation (used by every entity below):

```
SITE_BASE = `${site}${base}`        // e.g. https://racecraft-lab.github.io/racecraft-plugins-public
pageUrl(slug) = `${SITE_BASE}/${slug}/`   // trailingSlash: 'always'
```

---

## 1. Content page

A rendered documentation page. **19 at authoring time** (12 hand-authored +
7 generated). The feature adds the following attributes per page.

| Attribute | Source | Rule |
|-----------|--------|------|
| `description` (meta) | frontmatter (12 hand-authored) / `generate-reference-pages.mjs` (7 generated) | MUST be non-empty for every page (FR-009, FR-010); quality gate fails otherwise (SC-003) |
| canonical URL | Starlight built-in, from `site`+`base` | exactly one per page; no second source (FR-011, FR-027, SC-004) |
| visible "last updated" date | Starlight `lastUpdated: true` (git commit date; frontmatter override) | MUST match the sitemap `<lastmod>` (FR-018, SC-007) |
| `og:image` / `twitter:image` | `src/routeData.ts` → `og/[...slug].ts` | per-page card URL, titled for the page (FR-019, SC-008) |
| per-page `.md` variant | `[...slug].md.ts` (raw `body`) | one per content page, no orphans (FR-007, FR-008, SC-005) |
| JSON-LD `@graph` | `src/routeData.ts` | Organization + WebSite on every page (FR-013); + SoftwareApplication on the landing page; + Person (FR-014, FR-015) |

**Hand-authored set (12)** — each gains a `description:` frontmatter line:
`index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`, `first-run.md`,
`glossary.md`, `reference.md`, `security-and-trust.md`, `troubleshooting.md`,
`update-and-rollback.md`, `contribute-and-release.md`, `install/claude-code.md`,
`install/codex.md`.

**Generated set (7)** — `description:` emitted from the generator's
`renderPage()` frontmatter block: `reference/skills.md`, `reference/agents.md`,
`reference/manifests.md`, `reference/hooks.md`, `reference/scripts.md`,
`reference/tests.md`, `reference/source-vs-dist.md`.

**MDX caveat (FR-007)**: the 3 MDX pages emit raw `body` (including `import`/JSX)
in their `.md` variant — acceptable.

---

## 2. Crawler-access policy

The site-root `robots.txt` produced by the `robots.txt.ts` endpoint. Three tiers
plus a sitemap directive.

| Tier | User-agents | Directive | FR |
|------|-------------|-----------|-----|
| Training | `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot` | `Allow: /` (inverts sibling) | FR-002, FR-024 |
| Citation | `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User` | `Allow: /` | FR-001 |
| Default | `*` | `Allow: /` | FR-003 |
| Sitemap | — | `Sitemap: ${SITE_BASE}/sitemap-index.xml` | FR-004, FR-012 |

**Rules**:
- Emitted as `text/plain; charset=utf-8`, HTTP 200.
- The sitemap URL is derived from `site`+`base` (not `astro:env`), so it tracks
  the DOC-012 flip (FR-012, SC-010).
- The static `public/robots.txt` is removed so it cannot shadow the endpoint.

---

## 3. Structured-data entity graph

A single JSON-LD `@graph` object per page (`@context: "https://schema.org"`),
injected by `src/routeData.ts`, built by `src/lib/schema.ts`.

### Organization (every page — FR-013)
```
{ "@type": "Organization",
  "@id": `${SITE_BASE}#organization`,
  "name": "Racecraft Lab",
  "url": SITE_BASE,
  "logo": { "@type": "ImageObject", "url": `${SITE_BASE}/favicon.svg` },
  "sameAs": ["https://github.com/racecraft-lab"] }
```

### WebSite (every page — FR-013)
```
{ "@type": "WebSite",
  "@id": `${SITE_BASE}#website`,
  "url": SITE_BASE,
  "name": "Racecraft Public Plugins",
  "publisher": { "@id": `${SITE_BASE}#organization` } }   // publisher @id == Organization @id (SC-006 cross-ref)
```

### SoftwareApplication (landing page only — FR-014)
Gated by a `pluginPages` allowlist map (slug → metadata); currently only the
landing page (`index.mdx`, slug `''`) maps to speckit-pro.
```
{ "@type": "SoftwareApplication",
  "@id": `${SITE_BASE}#software-speckit-pro`,
  "name": "SpecKit Pro",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "macOS, Linux",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" } }   // free / OSS (SC-006)
```

### Person (every page — FR-015)
```
{ "@type": "Person",
  "@id": `${SITE_BASE}#person`,                  // NO PII in the @id fragment
  "name": "Fredrick Gabelmann",
  "worksFor": { "@id": `${SITE_BASE}#organization` },
  "sameAs": ["https://github.com/fgabelmannjr"] }
```

**Rules / invariants**:
- All `@id` and URL fields derive from `SITE_BASE` (DOC-012-flip-safe).
- `FAQPage` / `HowTo` MUST NOT be emitted (FR-028 sunset).
- The graph is justified as rich-results + entity disambiguation, **not** an
  answer-engine citation lever (FR-016 — documentation framing).

---

## 4. Agent-readable content

Two surfaces, both plain text generated from the site's own content.

| Surface | Producer | Output | FR |
|---------|----------|--------|-----|
| Whole-site digest | `starlight-llms-txt` plugin | `/llms.txt`, `/llms-full.txt`, `/llms-small.txt` | FR-006 |
| Per-page variant | `src/pages/[...slug].md.ts` (raw `body`) | `/<slug>.md` (one per content page) | FR-007, FR-008 |

**Rules**:
- Per-page variant served as `text/markdown`, `prerender = true`, one per
  `getCollection('docs')` entry — no orphans, none missing (FR-008, SC-005).
- Digest and per-page variant may overlap in content; both remain individually
  fetchable and must not conflict at build time (spec Edge Cases).

---

## 5. Sitemap

`sitemap-index.xml` + `sitemap-0.xml` from `@astrojs/sitemap` (promoted to a
direct dep, added to `integrations` with a custom `serialize()`).

| Field | Source | Rule |
|-------|--------|------|
| `loc` | `site`+`base` | absolute staging URL now; flips with DOC-012 (SC-010) |
| `lastmod` | single bulk `git log` walk → slug→date map (NOT per-file subprocess, withastro/astro#16803); frontmatter date override; OMIT if no history | valid ISO date from real change history, never build time (FR-017, SC-007) |

---

## 6. Success-metric definition

A documentation artifact (Markdown, under `docs/ai/specs/`). No runtime shape.

| Field | Content | Rule |
|-------|---------|------|
| Definition | "AI-discoverable" as an observable measure | concrete, observable (FR-021, SC-009) |
| Measurement source(s) | GSC "Generative AI" reports + GA4 AI-referrer channel group | named explicitly (FR-022, SC-009) |
| Numeric target | none | MUST NOT be asserted; deferred to post-launch baseline (FR-023) |
| Training-allow record | the FR-005 divergence from the sibling | recorded so it is not "fixed" back |

---

## State / lifecycle

None. Every shape above is produced deterministically at `astro build` time from
checked-in content + git history. There are no transitions, no mutable runtime
state, and no storage. Correctness is independent of the DOC-011 staging noindex
guard, which remains in place (FR-029, spec Edge Cases).
