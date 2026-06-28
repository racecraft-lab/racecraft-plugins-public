import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { expect, test } from '@playwright/test';

/**
 * DOC-014 (C7 / FR-017, FR-012 · SC-007, SC-010) — sitemap freshness signal.
 *
 * Fetches `/sitemap-index.xml` and the child `/sitemap-0.xml` from the built
 * site and asserts:
 *  - every `<loc>` resolves under `SITE_BASE` (derived from `site` + `base`),
 *    so the URLs track the DOC-012 launch flip and hardcode no production domain
 *    (FR-012, SC-010);
 *  - every `<lastmod>` is a valid ISO-8601 instant (FR-017, SC-007);
 *  - the `<lastmod>` is sourced from stable page history, not the build time or
 *    checkout HEAD. We prove this by picking content pages that this
 *    work-package does NOT modify (`glossary.md`, `first-run.md`) and asserting
 *    each sitemap `<lastmod>` is strictly BEFORE the test's run time and BEFORE
 *    the checkout HEAD date. A build-time `<lastmod>` or shallow/HEAD fallback
 *    would be at or after those anchors and fail this check.
 *
 * Chromium-only (the `desktop-chromium` Playwright project).
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C7
 */

const DOCS_SITE_DIR = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const REPO_ROOT = path.resolve(DOCS_SITE_DIR, '..');

// The absolute origin+base the sitemap `<loc>`/`<lastmod>` values are built from
// (astro.config.mjs `site` + `base`). Asserted against the XML CONTENT.
const SITE_BASE = 'https://racecraft-lab.github.io/racecraft-plugins-public';

// The sitemap files are served by the local preview under the configured `base`
// (verified: `astro preview` serves them at `/racecraft-plugins-public/...`, not
// at the host root). We FETCH them via these base-relative paths (resolved
// against Playwright's `baseURL`), while asserting the XML's absolute `<loc>`
// values against SITE_BASE above.
const SITEMAP_INDEX_PATH = 'sitemap-index.xml';
const SITEMAP_CHILD_PATH = 'sitemap-0.xml';

// Content pages NOT touched by this work-package; their newest commit dates must
// predate checkout HEAD and the smoke test run.
const GIT_SOURCED_PAGES = ['glossary', 'first-run'];

/** The commit date (ISO-8601) of HEAD itself — the current checkout commit. */
function gitHeadCommitDate() {
  return execFileSync('git', ['log', '-1', '--format=%cI'], {
    cwd: REPO_ROOT,
    encoding: 'utf-8',
  }).trim();
}

/** Extract all `<loc>` values from a sitemap XML string. */
function locs(xml) {
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
}

/** Extract `[{ loc, lastmod }]` pairs (lastmod may be undefined when the element is omitted). */
function urlEntries(xml) {
  return [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((m) => {
    const block = m[1];
    const loc = block.match(/<loc>([^<]+)<\/loc>/)?.[1];
    const lastmod = block.match(/<lastmod>([^<]+)<\/lastmod>/)?.[1];
    return { loc, lastmod };
  });
}

const ISO_8601 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

async function fetchText(request, url) {
  const response = await request.get(url);
  expect(response.status(), `${url} should return 200`).toBe(200);
  return response.text();
}

test.describe('DOC-014 sitemap freshness', () => {
  test('sitemap index lists a child sitemap under SITE_BASE', async ({ request }) => {
    const indexXml = await fetchText(request, SITEMAP_INDEX_PATH);
    const childSitemaps = [...indexXml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
    expect(childSitemaps.length).toBeGreaterThan(0);
    for (const child of childSitemaps) {
      expect(child.startsWith(`${SITE_BASE}/`)).toBe(true);
    }
  });

  test('every loc resolves under SITE_BASE (no hardcoded production domain)', async ({ request }) => {
    const xml = await fetchText(request, SITEMAP_CHILD_PATH);
    const urls = locs(xml);
    expect(urls.length).toBeGreaterThan(0);
    for (const url of urls) {
      expect(url.startsWith(`${SITE_BASE}/`), `${url} must be under SITE_BASE`).toBe(true);
    }
  });

  test('every lastmod is a valid ISO-8601 instant', async ({ request }) => {
    const xml = await fetchText(request, SITEMAP_CHILD_PATH);
    const entries = urlEntries(xml);
    const withDates = entries.filter((e) => e.lastmod);
    // At least the git-sourced pages must carry a date.
    expect(withDates.length).toBeGreaterThan(0);
    for (const { loc, lastmod } of withDates) {
      expect(lastmod, `${loc} <lastmod> must match ISO-8601`).toMatch(ISO_8601);
      expect(Number.isNaN(Date.parse(lastmod)), `${loc} <lastmod> must parse as a date`).toBe(false);
    }
  });

  test('lastmod is the page git commit date, not the build time', async ({ request }) => {
    const xml = await fetchText(request, SITEMAP_CHILD_PATH);
    const entries = urlEntries(xml);
    const runStart = Date.now();
    const headIso = gitHeadCommitDate();
    const headMs = Date.parse(headIso);

    for (const slug of GIT_SOURCED_PAGES) {
      const wantLoc = `${SITE_BASE}/${slug}/`;
      const entry = entries.find((e) => e.loc === wantLoc);
      expect(entry, `sitemap must include ${wantLoc}`).toBeTruthy();
      expect(entry.lastmod, `${wantLoc} must carry a <lastmod> from git history`).toBeTruthy();
      const entryMs = Date.parse(entry.lastmod);

      // Strictly in the past relative to this test run; a build-time date would
      // be ~now and fail this guard.
      expect(
        entryMs,
        `${wantLoc} <lastmod> must be in the past, not the build/run time`,
      ).toBeLessThan(runStart);

      // Shallow-checkout guard (rp-review P2.4): these stable pages are not
      // touched by the checkout tip, so their sitemap dates must predate HEAD.
      // A depth-1 fallback collapses page dates to HEAD and fails here.
      expect(
        entryMs,
        `${wantLoc}: sitemap git date ${entry.lastmod} must predate the HEAD commit date ${headIso} (shallow-clone guard)`,
      ).toBeLessThan(headMs);
    }
  });
});
