import { expect, test } from '@playwright/test';

// DOC-014 C5 + C4 / FR-006, FR-007, FR-008 · SC-005, US3 (coding-agent retrieval).
//
// Two agent-readable retrieval surfaces are asserted here, both served at
// distinct build-time URLs under the configured base path (no Accept-header
// content negotiation — FR-028). Fetches are relative to `baseURL` (which
// already ends in `/racecraft-plugins-public/`), matching the smoke spec and
// `seo-robots-txt.spec.mjs` route convention.
//
//   1. Whole-site digests (C5, FR-006) — `llms.txt`, `llms-full.txt`,
//      `llms-small.txt` from `starlight-llms-txt`. Each MUST return 200 with a
//      non-empty plain-text body.
//   2. Per-page Markdown variants (C4, FR-007/FR-008) — `<page-path>.md` from
//      the custom `src/pages/[...slug].md.ts` endpoint. Each content page MUST
//      expose its raw `body` as text/markdown at HTTP 200, with the variant
//      content corresponding to the rendered page (no orphaned/missing pages).

const DIGESTS = Object.freeze(['llms.txt', 'llms-full.txt', 'llms-small.txt']);

// Representative content pages (a markdown page, a nested reference page, and
// the index/landing page) plus a snippet that MUST appear in each page's raw
// `body`. `mdPath` is the per-page text variant URL relative to `baseURL`; it is
// the rendered page path with a `.md` suffix (the root landing page is served at
// `index.md`). `mustContain` is body prose — NOT the frontmatter `title`, which
// the endpoint does not include because it returns the raw `body` only (so e.g.
// the Glossary page asserts on its "Marketplace" section heading, not the word
// "Glossary"). The acceptable media types are text/markdown (what the endpoint
// serves) with text/plain tolerated for robustness.
const PER_PAGE_VARIANTS = Object.freeze([
  { mdPath: 'glossary.md', mustContain: 'Marketplace' },
  { mdPath: 'reference/skills.md', mustContain: 'speckit' },
  { mdPath: 'index.md', mustContain: 'spec' },
]);

const MARKDOWN_CONTENT_TYPES = ['text/markdown', 'text/plain'];

test.describe('DOC-014 whole-site digests (C5 / FR-006)', () => {
  for (const digest of DIGESTS) {
    test(`${digest} returns 200 with a non-empty plain-text body`, async ({ request, baseURL }) => {
      const response = await request.get(new URL(digest, baseURL).toString());
      expect(response.status(), `${digest} must return HTTP 200`).toBe(200);
      const body = await response.text();
      expect(body.trim().length, `${digest} body must be non-empty`).toBeGreaterThan(0);
    });
  }
});

test.describe('DOC-014 per-page Markdown variants (C4 / FR-007, FR-008)', () => {
  for (const variant of PER_PAGE_VARIANTS) {
    test(`${variant.mdPath} returns 200 text/markdown with the page's content`, async ({
      request,
      baseURL,
    }) => {
      const response = await request.get(new URL(variant.mdPath, baseURL).toString());
      expect(response.status(), `${variant.mdPath} must return HTTP 200`).toBe(200);

      const contentType = response.headers()['content-type'] ?? '';
      expect(
        MARKDOWN_CONTENT_TYPES.some((type) => contentType.includes(type)),
        `${variant.mdPath} must be served as text/markdown (or text/plain); got "${contentType}"`,
      ).toBe(true);

      const body = await response.text();
      expect(body.trim().length, `${variant.mdPath} body must be non-empty`).toBeGreaterThan(0);
      expect(
        body,
        `${variant.mdPath} body must contain content from the rendered page`,
      ).toContain(variant.mustContain);
    });
  }
});
