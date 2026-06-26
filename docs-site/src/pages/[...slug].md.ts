import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';

/**
 * Per-page agent-readable Markdown variant (DOC-014, C4 / FR-007, FR-008 · US3).
 *
 * Serves each content page's raw Markdown `body` at a distinct, build-time
 * `<page-path>.md` URL so coding agents (Cursor, Claude Code, Copilot) can fetch
 * a single page cheaply without scraping rendered HTML. This is the per-page
 * companion to the whole-site `starlight-llms-txt` digests (C5); the two
 * surfaces may overlap in content yet remain independently fetchable.
 *
 * Dependency-free custom endpoint (D3): iterating `getCollection('docs')`
 * guarantees exactly one `.md` route per content page — no orphaned variant (a
 * `.md` with no rendered page) and no content page missing a variant (FR-008).
 * The 3 MDX pages (`index.mdx`, `choose-your-path.mdx`, `spec-kit-lifecycle.mdx`)
 * emit their raw `body`, which includes `import`/JSX; this is acceptable per
 * FR-007 (the variant returns source `body`, not rendered prose).
 *
 * `prerender = true` — produced at build time and served as a static file, with
 * no request-time content negotiation (FR-028): the variant lives at its own URL
 * rather than relying on an `Accept: text/markdown` header that no crawler
 * honors for a static site.
 *
 * URL shape: the route param is derived with the same normalization Starlight
 * applies to its page routes (`@astrojs/starlight/utils/slugs.ts` `slugToParam`)
 * so the `.md` URL is the rendered page path plus a `.md` suffix and the two stay
 * aligned under `base`/`trailingSlash`. The root landing page (`index`, whose
 * page route param is empty) is served at `index.md`.
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C4
 */
export const prerender = true;

/**
 * Convert a docs collection entry id to its route param, mirroring Starlight's
 * own `slugToParam` (strip a leading/standalone `index`, drop a trailing
 * `/index`, and normalize). The root entry (`index`) has no page param, so it is
 * mapped to the literal `index` here to give it an `index.md` URL.
 */
function slugToMdParam(id: string): string {
  if (id === 'index' || id === '' || id === '/') return 'index';
  const stripped = id.endsWith('/index') ? id.slice(0, -'/index'.length) : id;
  return stripped.normalize();
}

export const getStaticPaths: GetStaticPaths = async () => {
  const docs = await getCollection('docs');
  return docs.map((entry) => ({
    params: { slug: slugToMdParam(entry.id) },
    props: { body: entry.body ?? '' },
  }));
};

export const GET: APIRoute = ({ props }) => {
  const body = (props as { body?: string }).body ?? '';
  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
