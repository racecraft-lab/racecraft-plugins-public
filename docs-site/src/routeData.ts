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
 *  - WP5/T029 (TODO below): push per-page `og:image` / `twitter:image` `<meta>`
 *    tags pointing at the `og/[...slug].ts` card for the current route, onto the
 *    SAME `head` array.
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

/** Build the per-route `@graph`: site-wide entities + SoftwareApplication on plugin pages. */
function buildRouteGraph(slug: string) {
  const items: SchemaItem[] = [
    buildOrganizationSchema(SITE_BASE),
    buildWebSiteSchema(SITE_BASE),
    buildPersonSchema(SITE_BASE),
  ];

  const pluginMeta = pluginPages[slug];
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

  // TODO(WP5/T029): push og:image / twitter:image <meta> tags for this route
  // onto starlightRoute.head (pointing at og/[...slug].ts for the current slug).
});
