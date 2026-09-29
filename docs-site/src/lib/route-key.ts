/**
 * Map a docs collection or route id to the key shared by three consumers: the
 * OG card endpoint (`src/pages/og/[...slug].ts`), the `og:image` URL built in
 * `src/routeData.ts`, and the per-page Markdown endpoint
 * (`src/pages/[...slug].md.ts`). One helper keeps the card a page references
 * identical to the card the endpoint generates. Root (`index`, empty or `/`)
 * maps to `index`; otherwise the id loses any trailing `/index`.
 */
export function routeKey(id: string): string {
  if (id === 'index' || id === '' || id === '/') return 'index';
  return (id.endsWith('/index') ? id.slice(0, -'/index'.length) : id).normalize();
}
