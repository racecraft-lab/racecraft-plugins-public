import { test, expect } from '@playwright/test';

/**
 * DOC-014 per-page Open Graph cards (C6 / FR-019, FR-020 · US5).
 *
 * Asserts every content page references its OWN per-page card (not a single
 * site-wide image), that the card is served as a real PNG, and that adding the
 * OG tags did not clobber the WP4 JSON-LD structured data on the same page.
 */

const SITE_BASE = 'https://racecraft-lab.github.io/racecraft-plugins-public';

// Paths are relative to the configured baseURL (which already includes the
// `/racecraft-plugins-public/` base), mirroring the other SEO specs.
test('a content page references its own per-page og:image and twitter:image', async ({ page }) => {
  await page.goto('glossary/');

  // DOC-014 adds the per-page image tags Starlight lacks (it has no default
  // image). Starlight already owns `twitter:card`, so DOC-014 must NOT duplicate it.
  const ogImage = await page.locator('head meta[property="og:image"]').getAttribute('content');
  const twImage = await page.locator('head meta[name="twitter:image"]').getAttribute('content');

  expect(ogImage).toBe(`${SITE_BASE}/og/glossary.png`);
  expect(twImage).toBe(`${SITE_BASE}/og/glossary.png`);

  // Exactly one image tag each (no duplicate emission).
  await expect(page.locator('head meta[property="og:image"]')).toHaveCount(1);
  await expect(page.locator('head meta[name="twitter:image"]')).toHaveCount(1);
});

test('different pages reference different per-page cards (not one generic image)', async ({ page }) => {
  await page.goto('first-run/');
  const firstRun = await page.locator('head meta[property="og:image"]').getAttribute('content');
  expect(firstRun).toBe(`${SITE_BASE}/og/first-run.png`);

  await page.goto('troubleshooting/');
  const troubleshooting = await page.locator('head meta[property="og:image"]').getAttribute('content');
  expect(troubleshooting).toBe(`${SITE_BASE}/og/troubleshooting.png`);

  expect(firstRun).not.toBe(troubleshooting);
});

test('the per-page OG card is served as a non-empty PNG', async ({ request }) => {
  const res = await request.get('og/glossary.png');
  expect(res.status()).toBe(200);
  expect(res.headers()['content-type']).toContain('image/png');
  const body = await res.body();
  expect(body.length).toBeGreaterThan(1000);
});

test('the JSON-LD structured data is still present alongside the OG tags (WP4 intact)', async ({ page }) => {
  await page.goto('glossary/');
  const ldCount = await page.locator('head script[type="application/ld+json"]').count();
  expect(ldCount).toBeGreaterThanOrEqual(1);
});
