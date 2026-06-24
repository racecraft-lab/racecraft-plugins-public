import { defineConfig, passthroughImageService } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';

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
      plugins: [starlightLinksValidator()],
      customCss: ['./src/styles/brand.css'],
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
  ],
});
