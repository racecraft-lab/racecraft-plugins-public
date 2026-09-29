import { getCollection } from 'astro:content';
import { OGImageRoute } from 'astro-og-canvas';

import { routeKey } from '../../lib/route-key';

/**
 * Per-page Open Graph card endpoint (DOC-014, C6 / FR-019, FR-020 · US5).
 *
 * Generates one social-preview PNG per content page, titled/labelled for that
 * page (not a single site-wide image). `astro-og-canvas` renders each card at
 * build time via `canvaskit-wasm`/Skia, so it is orthogonal to the site's
 * `passthroughImageService` (it never touches Astro's image pipeline). The
 * route middleware (`src/routeData.ts`) references each page's own card from
 * `<head>` via `og:image`/`twitter:image`.
 *
 * Cards are a text-only branded layout: a brand background + an accent edge +
 * the page title and description, rendered in Space Grotesk (the DOC-013 brand
 * display face). canvaskit/Skia cannot decode the repo's `woff2` fonts or `svg`
 * logo, so the card draws from committed `.ttf` build assets under
 * `src/assets/og/` (a logo image is intentionally omitted — a text card fully
 * satisfies FR-019/FR-020).
 *
 * Static output prerenders this route (the site has no adapter), so every card
 * is emitted to `dist/og/<slug>.png` at build time.
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C6
 */

interface CardPage {
  title: string;
  description: string;
}

const docs = await getCollection('docs');

const pages: Record<string, CardPage> = Object.fromEntries(
  docs.map((entry) => [
    routeKey(entry.id),
    {
      title: entry.data.title,
      description: entry.data.description ?? '',
    },
  ]),
);

export const { getStaticPaths, GET } = await OGImageRoute({
  pages,
  getImageOptions: (_path, page: CardPage) => ({
    title: page.title,
    description: page.description,
    // Brand-styled, text-only card (FR-019/FR-020): dark background + blue
    // accent edge, the same accent as --sl-color-accent in src/styles/brand.css.
    bgGradient: [
      [12, 12, 16],
      [24, 24, 32],
    ],
    border: { color: [60, 137, 198], width: 12, side: 'inline-start' },
    padding: 72,
    font: {
      title: {
        color: [255, 255, 255],
        size: 64,
        lineHeight: 1.1,
        weight: 'Bold',
        families: ['Space Grotesk'],
      },
      description: {
        color: [176, 180, 194],
        size: 30,
        lineHeight: 1.3,
        weight: 'Medium',
        families: ['Space Grotesk'],
      },
    },
    fonts: [
      './src/assets/og/SpaceGrotesk-700.ttf',
      './src/assets/og/SpaceGrotesk-500.ttf',
    ],
  }),
});
