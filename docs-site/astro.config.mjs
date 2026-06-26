import { defineConfig, passthroughImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';

export default defineConfig({
  site: 'https://racecraft-lab.github.io',
  base: '/racecraft-plugins-public',
  trailingSlash: 'always',
  // DOC-013 — the brand logo/mark assets are SVG vectors that should be served
  // as-is; the passthrough image service avoids a Sharp rasterization dependency
  // that docs-site does not ship as a direct dependency.
  image: { service: passthroughImageService() },
  integrations: [
    starlight({
      title: 'Racecraft Public Plugins',
      plugins: [starlightLinksValidator(), starlightLlmsTxt()],
      customCss: ['./src/styles/brand.css'],
      // DOC-014 (D7) — visible "last updated" stamp from the git commit date,
      // consistent with the sitemap <lastmod> (frontmatter date override allowed).
      lastUpdated: true,
      // DOC-014 (D2) — route-data middleware is the single head-injection
      // mechanism (JSON-LD @graph + per-page OG/twitter tags); Starlight 0.40
      // designates a Head.astro override "a last resort".
      routeMiddleware: './src/routeData.ts',
      logo: {
        light: './src/assets/logo.svg',
        dark: './src/assets/logo-light.svg',
        replacesTitle: true,
        alt: 'Racecraft',
      },
      favicon: '/favicon.svg',
      // DOC-012 removes this staging-only indexing guard at public launch.
      head: [
        {
          tag: 'meta',
          attrs: { name: 'robots', content: 'noindex, nofollow' },
        },
        // DOC-013 — preload only the two above-the-fold faces (hero display +
        // body regular); the other three faces use font-display: swap.
        {
          tag: 'link',
          attrs: {
            rel: 'preload',
            href: '/racecraft-plugins-public/fonts/space-grotesk-700.woff2',
            as: 'font',
            type: 'font/woff2',
            crossorigin: 'anonymous',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'preload',
            href: '/racecraft-plugins-public/fonts/geist-400.woff2',
            as: 'font',
            type: 'font/woff2',
            crossorigin: 'anonymous',
          },
        },
        // DOC-013 — brand favicon set + theme color (base-path-prefixed hrefs).
        {
          tag: 'link',
          attrs: {
            rel: 'icon',
            type: 'image/png',
            sizes: '32x32',
            href: '/racecraft-plugins-public/favicon-32x32.png',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'icon',
            type: 'image/png',
            sizes: '16x16',
            href: '/racecraft-plugins-public/favicon-16x16.png',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'apple-touch-icon',
            sizes: '180x180',
            href: '/racecraft-plugins-public/apple-touch-icon.png',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'manifest',
            href: '/racecraft-plugins-public/site.webmanifest',
          },
        },
        {
          tag: 'meta',
          attrs: { name: 'theme-color', content: '#dc143c' },
        },
      ],
      sidebar: [
        {
          label: 'Tutorials',
          items: ['index', 'install/claude-code', 'install/codex', 'first-run'],
        },
        {
          label: 'How-to',
          items: ['choose-your-path', 'troubleshooting', 'update-and-rollback', 'contribute-and-release'],
        },
        {
          label: 'Reference',
          items: [
            'reference',
            'reference/skills',
            'reference/agents',
            'reference/manifests',
            'reference/hooks',
            'reference/scripts',
            'reference/tests',
            'reference/source-vs-dist',
            'glossary',
          ],
        },
        {
          label: 'Explanation',
          items: ['security-and-trust', 'spec-kit-lifecycle'],
        },
      ],
    }),
    // DOC-014 (D6) — promote @astrojs/sitemap to a direct dep so we can attach a
    // custom serialize(). Starlight 0.40 defers to a user-provided @astrojs/sitemap,
    // so adding it directly does NOT raise a duplicate-instance error.
    //
    // NOTE: the integration's top-level `lastmod` option is intentionally NOT set —
    // a page with no git history must be able to OMIT <lastmod> entirely (the
    // sitemap protocol allows it), and the default top-level lastmod would be the
    // build time, which Google distrusts (FR-017).
    sitemap({
      serialize(item) {
        // TODO(WP4/T021): resolve each page's <lastmod> from a SINGLE bulk
        // `git log` walk (slug→ISO-date map built once; NOT one subprocess per
        // page — the O(pages) slow path, withastro/astro#16803), honoring a
        // per-page frontmatter date override. For a page with no commit history,
        // leave `item.lastmod` undefined so @astrojs/sitemap omits <lastmod>.
        // MUST NOT default to build time.
        return item;
      },
    }),
  ],
});
