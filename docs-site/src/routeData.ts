import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import { base, site } from 'astro:config/server';

import {
  buildGraph,
  buildOrganizationSchema,
  buildPersonSchema,
  buildSoftwareApplicationSchema,
  buildWebSiteSchema,
  pluginPages,
  type SchemaItem,
} from './lib/schema';

/**
 * Starlight route-data middleware (DOC-014, D2).
 *
 * Runs for every Starlight route and is the SINGLE head-injection mechanism for
 * this feature (Starlight 0.40 designates a `Head.astro` override "a last resort").
 * Registered via `routeMiddleware: './src/routeData.ts'` in `astro.config.mjs`.
 *
 * Responsibilities:
 *  - WP4/T020 (this block): push ONE `<script type="application/ld+json">` per
 *    page — Organization + WebSite + Person site-wide (FR-013/FR-015), plus a
 *    SoftwareApplication when the route slug is in the `pluginPages` allowlist
 *    (the landing page — FR-014). The WebSite `publisher["@id"]` equals the
 *    Organization `@id` (C2 cross-reference). NO `FAQPage`/`HowTo` (FR-028).
 *  - WP5/T029 (implemented below): pushes per-page `og:image` / `twitter:image`
 *    `<meta>` tags pointing at the `og/[...slug].ts` card for the current route,
 *    onto the SAME `head` array.
 *
 * `SITE_BASE` derives from `site` + `base` (via `astro:config/server`, the same
 * source `robots.txt.ts` uses), so every `@id`/URL finalizes automatically at the
 * DOC-012 launch flip with no hardcoded production domain (FR-012).
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C2, C6
 */

/**
 * Absolute `${site}${base}` with no trailing slash (e.g.
 * `https://racecraft-lab.github.io/racecraft-plugins-public`). `site` is
 * statically configured (Constraints); if it is unset the build throws here
 * rather than emit a graph with a relative/blank `@id`.
 */
function siteBase(): string {
  if (!site) {
    throw new Error(
      'routeData: `site` is not configured; cannot derive structured-data @id values.',
    );
  }
  // Astro normalizes `base` (defaults to "/"); strip a trailing slash so
  // `${SITE_BASE}#organization` and `${SITE_BASE}/favicon.svg` join cleanly.
  const joined = `${site.replace(/\/$/, '')}${base}`;
  return joined.replace(/\/$/, '');
}

const SITE_BASE = siteBase();

/**
 * Map a route id to its OG card key — identical to `og/[...slug].ts`'s mapping so
 * the `og:image` URL references the card that endpoint actually generates. Root
 * (`index` or empty) → `index`; otherwise the id minus any trailing `/index`.
 */
function ogCardKey(id: string): string {
  if (id === 'index' || id === '' || id === '/') return 'index';
  return (id.endsWith('/index') ? id.slice(0, -'/index'.length) : id).normalize();
}

/** Build the per-route `@graph`: site-wide entities + SoftwareApplication on plugin pages. */
function buildRouteGraph(slug: string) {
  const items: SchemaItem[] = [
    buildOrganizationSchema(SITE_BASE),
    buildWebSiteSchema(SITE_BASE),
    buildPersonSchema(SITE_BASE),
  ];

  // Normalize landing-page route-id variants (`index` / `/`) to the `''` key
  // pluginPages uses, so the SoftwareApplication entity is emitted regardless of
  // which homepage route-id form Starlight reports (FR-014 robustness).
  const pluginKey = slug === 'index' || slug === '/' ? '' : slug;
  const pluginMeta = pluginPages[pluginKey];
  if (pluginMeta) {
    items.push(buildSoftwareApplicationSchema(SITE_BASE, pluginMeta));
  }

  return buildGraph(items);
}

export const onRequest = defineRouteMiddleware((context) => {
  const { starlightRoute } = context.locals;
  const slug = starlightRoute.id;

  // WP4/T020 — one JSON-LD <script> built from src/lib/schema.ts.
  const graph = buildRouteGraph(slug);
  starlightRoute.head.push({
    tag: 'script',
    attrs: { type: 'application/ld+json' },
    content: JSON.stringify(graph),
  });

  // WP5/T029 — per-page Open Graph card (astro-og-canvas, C6 / FR-019, FR-020).
  // og:image / twitter:image point at THIS route's card from `og/[...slug].ts`,
  // referenced only in <head> (not an on-page / render-blocking asset). The card
  // URL derives from SITE_BASE, so it finalizes at the DOC-012 launch flip.
  // Starlight 0.40 already emits `twitter:card = summary_large_image`, so we add
  // ONLY the image tags it lacks (no default image) — never a duplicate card tag.
  const ogImage = `${SITE_BASE}/og/${ogCardKey(slug)}.png`;
  starlightRoute.head.push(
    { tag: 'meta', attrs: { property: 'og:image', content: ogImage } },
    { tag: 'meta', attrs: { name: 'twitter:image', content: ogImage } },
  );
});
