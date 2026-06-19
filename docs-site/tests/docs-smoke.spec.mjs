import { expect, test } from '@playwright/test';

const DOC010_ROUTES = [
  { logicalPath: '/', heading: 'Start' },
  { logicalPath: '/choose-your-path/', heading: 'Choose Your Path' },
  { logicalPath: '/spec-kit-lifecycle/', heading: 'Spec Kit Lifecycle' },
  { logicalPath: '/glossary/', heading: 'Glossary' },
  { logicalPath: '/reference/skills/', heading: 'Skills Reference' },
  { logicalPath: '/contribute-and-release/', heading: 'Contribute & Release' },
];

const DOC010_DEEP_LINKS = [
  {
    logicalPath: '/glossary/#marketplace',
    target: '#marketplace',
    heading: 'Marketplace',
  },
  {
    logicalPath: '/reference/skills/#speckit-status',
    target: '#speckit-status',
    heading: 'Speckit Status',
  },
  {
    logicalPath: '/spec-kit-lifecycle/#what-each-gate-means',
    target: '#what-each-gate-means',
    heading: 'What Each Gate Means',
  },
  {
    logicalPath: '/contribute-and-release/#maintainer-release-readiness',
    target: '#maintainer-release-readiness',
    heading: 'Maintainer Release Readiness',
  },
];

function routeUrl(logicalPath) {
  return logicalPath === '/' ? './' : `.${logicalPath}`;
}

async function expectConfiguredViewport(page, projectName) {
  const viewport = page.viewportSize();
  expect(viewport, `${projectName} should define a fixed smoke viewport`).not.toBeNull();

  if (projectName.includes('mobile')) {
    expect(viewport.width, `${projectName} should use a mobile-width viewport`).toBeLessThanOrEqual(500);
    return;
  }

  expect(viewport.width, `${projectName} should use a desktop-width viewport`).toBeGreaterThanOrEqual(1024);
}

test.describe('DOC-010 route smoke', () => {
  for (const route of DOC010_ROUTES) {
    test(`${route.logicalPath} loads the route heading and configured viewport`, async ({ page }, testInfo) => {
      await expectConfiguredViewport(page, testInfo.project.name);
      await page.goto(routeUrl(route.logicalPath));

      await expect(page.getByRole('main')).toBeVisible();
      await expect(page.getByRole('heading', { level: 1, name: route.heading })).toBeVisible();
    });
  }

  test('homepage search finds support-oriented guidance', async ({ page }, testInfo) => {
    await expectConfiguredViewport(page, testInfo.project.name);
    await page.goto(routeUrl('/'));

    await page.getByRole('button', { name: /search/i }).first().click();
    const searchInput = page.getByRole('searchbox').or(page.getByRole('textbox', { name: /search/i })).first();
    await expect(searchInput).toBeVisible();

    await searchInput.fill('troubleshooting install');

    await expect(page.getByRole('link', { name: /Troubleshooting/i }).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test('representative deep links resolve to intended sections', async ({ page }, testInfo) => {
    await expectConfiguredViewport(page, testInfo.project.name);

    for (const sample of DOC010_DEEP_LINKS) {
      await page.goto(routeUrl(sample.logicalPath));

      const target = page.locator(sample.target);
      await expect(target).toBeVisible();
      await expect(target).toContainText(sample.heading);
      await expect(page).toHaveURL(new RegExp(`${sample.target}$`));
    }
  });

  test('SafeInstallAids exposes bounded controls and copyable guidance', async ({ page }, testInfo) => {
    await expectConfiguredViewport(page, testInfo.project.name);
    await page.goto(routeUrl('/choose-your-path/'));

    const safeAids = page.locator('[data-safe-install-aids]');
    await expect(safeAids).toBeVisible();
    await expect(safeAids.getByRole('heading', { name: 'Safe Install Selector' })).toBeVisible();
    await expect(safeAids.getByText(/does not execute local commands/i)).toBeVisible();
    await expect(safeAids.getByText(/does not accept user JSON/i)).toBeVisible();

    await safeAids.getByRole('radio', { name: /Install speckit-pro from this repository in Codex/i }).check();
    await expect(safeAids.locator('#safe-aids-selector-status')).toContainText(
      'Selected path: Install speckit-pro from this repository in Codex.',
    );
    await expect(safeAids.getByRole('heading', { name: 'Static Selector Fallback' })).toBeVisible();
    await expect(safeAids.getByRole('button', { name: 'Copy' }).first()).toBeVisible();
    await expect(safeAids.getByRole('heading', { name: 'Repository Manifest Checker' })).toBeVisible();
  });

  test('LifecycleFlow exposes static fallback and phase evidence', async ({ page }, testInfo) => {
    await expectConfiguredViewport(page, testInfo.project.name);
    await page.goto(routeUrl('/spec-kit-lifecycle/'));

    const lifecycleFlow = page.locator('[data-lifecycle-flow]');
    await expect(lifecycleFlow).toBeVisible();
    await expect(lifecycleFlow.getByRole('heading', { name: 'Lifecycle Artifact Flow' })).toBeVisible();
    await expect(lifecycleFlow.getByText(/Static fallback: No JavaScript is required/i)).toBeVisible();
    await expect(lifecycleFlow.getByRole('link', { name: 'Lifecycle overview table' })).toHaveAttribute(
      'href',
      '#lifecycle-overview',
    );
    await expect(lifecycleFlow.locator('#lifecycle-step-implement')).toContainText('Implement');
    await expect(page.locator('#what-each-gate-means')).toBeVisible();
  });
});
