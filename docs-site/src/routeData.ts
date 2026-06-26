import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

/**
 * Starlight route-data middleware (DOC-014, D2).
 *
 * Runs for every Starlight route and is the SINGLE head-injection mechanism for
 * this feature (Starlight 0.40 designates a `Head.astro` override "a last resort").
 * Registered via `routeMiddleware: './src/routeData.ts'` in `astro.config.mjs`.
 *
 * WP1 (Foundation) lands this wired but with an empty body. Later work-packages
 * fill it in:
 *  - WP4/T020: build the JSON-LD `@graph` from `src/lib/schema.ts` (Organization +
 *    WebSite + Person on every page; SoftwareApplication on `pluginPages` entries),
 *    derive `SITE_BASE` from `context.site` + the configured base, and push one
 *    `<script type="application/ld+json">` onto `context.locals.starlightRoute.head`.
 *  - WP5/T029: push per-page `og:image` / `twitter:image` `<meta>` tags pointing at
 *    the `og/[...slug].ts` card for the current route.
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C2, C6
 */
export const onRequest = defineRouteMiddleware((context) => {
  // TODO(WP4/T020): push JSON-LD <script> built from src/lib/schema.ts.
  // TODO(WP5/T029): push og:image / twitter:image <meta> tags for this route.
  void context;
});
