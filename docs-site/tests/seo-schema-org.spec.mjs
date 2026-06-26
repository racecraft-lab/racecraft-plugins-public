import { expect, test } from '@playwright/test';

/**
 * DOC-014 (C2 / FR-013, FR-014, FR-015, FR-016, FR-028 · SC-006) — JSON-LD
 * structured-data graph.
 *
 * The route-data middleware (`src/routeData.ts`) injects exactly one
 * `<script type="application/ld+json">` per page whose JSON is
 * `{ "@context": "https://schema.org", "@graph": [...] }`. These tests parse that
 * graph from the rendered HTML and assert the cross-reference invariant and the
 * per-page gating that the contract requires:
 *  - Organization `@id` EQUALS WebSite `publisher["@id"]` (C2 cross-reference);
 *  - a Person entity with `name === "Fredrick Gabelmann"` is present site-wide;
 *  - the landing page carries a SoftwareApplication with `offers.price === "0"`,
 *    and a non-plugin page (e.g. `/glossary/`) does NOT;
 *  - NO `FAQPage` / `HowTo` `@type` anywhere (FR-028 sunset).
 *
 * Chromium-only (the `desktop-chromium` Playwright project), matching the
 * existing docs-smoke spec.
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C2
 */

function routeUrl(logicalPath) {
  return logicalPath === '/' ? './' : `.${logicalPath}`;
}

/**
 * Parse every `application/ld+json` block on the page and return the flattened
 * list of `@graph` items across all blocks (this feature emits a single block,
 * but reading all of them keeps the assertion robust to head ordering).
 */
async function readGraphItems(page) {
  const blocks = await page.locator('script[type="application/ld+json"]').allTextContents();
  const items = [];
  for (const raw of blocks) {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed['@graph'])) {
      items.push(...parsed['@graph']);
    } else {
      items.push(parsed);
    }
  }
  return items;
}

function findByType(items, type) {
  return items.filter((item) => {
    const t = item['@type'];
    return Array.isArray(t) ? t.includes(type) : t === type;
  });
}

test.describe('DOC-014 JSON-LD structured data', () => {
  test('every page carries exactly one ld+json block with @context schema.org', async ({ page }) => {
    await page.goto(routeUrl('/glossary/'));
    const blocks = page.locator('script[type="application/ld+json"]');
    await expect(blocks).toHaveCount(1);
    const parsed = JSON.parse(await blocks.first().textContent());
    expect(parsed['@context']).toBe('https://schema.org');
    expect(Array.isArray(parsed['@graph'])).toBe(true);
  });

  test('Organization @id equals WebSite publisher @id (C2 cross-reference)', async ({ page }) => {
    await page.goto(routeUrl('/glossary/'));
    const items = await readGraphItems(page);

    const orgs = findByType(items, 'Organization');
    const sites = findByType(items, 'WebSite');
    expect(orgs, 'an Organization entity must be present on every page').toHaveLength(1);
    expect(sites, 'a WebSite entity must be present on every page').toHaveLength(1);

    const org = orgs[0];
    const website = sites[0];
    expect(org['@id']).toBeTruthy();
    expect(website.publisher).toBeTruthy();
    expect(website.publisher['@id']).toBe(org['@id']);
  });

  test('a Person entity named Fredrick Gabelmann is present site-wide', async ({ page }) => {
    await page.goto(routeUrl('/glossary/'));
    const items = await readGraphItems(page);

    const persons = findByType(items, 'Person');
    expect(persons, 'a Person entity must be present on every page').toHaveLength(1);
    expect(persons[0].name).toBe('Fredrick Gabelmann');
  });

  test('the landing page emits a SoftwareApplication with offers.price "0"', async ({ page }) => {
    await page.goto(routeUrl('/'));
    const items = await readGraphItems(page);

    const apps = findByType(items, 'SoftwareApplication');
    expect(apps, 'the landing page must carry a SoftwareApplication entity').toHaveLength(1);
    expect(apps[0].offers).toBeTruthy();
    expect(apps[0].offers.price).toBe('0');
  });

  test('a non-plugin page does NOT emit a SoftwareApplication', async ({ page }) => {
    await page.goto(routeUrl('/glossary/'));
    const items = await readGraphItems(page);
    expect(findByType(items, 'SoftwareApplication')).toHaveLength(0);
  });

  test('no FAQPage or HowTo entity is emitted anywhere (FR-028 sunset)', async ({ page }) => {
    for (const logicalPath of ['/', '/glossary/']) {
      await page.goto(routeUrl(logicalPath));
      const items = await readGraphItems(page);
      expect(findByType(items, 'FAQPage'), `${logicalPath} must not emit FAQPage`).toHaveLength(0);
      expect(findByType(items, 'HowTo'), `${logicalPath} must not emit HowTo`).toHaveLength(0);
    }
  });
});
