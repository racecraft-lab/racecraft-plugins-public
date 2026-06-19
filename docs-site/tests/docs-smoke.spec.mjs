import { expect, test } from '@playwright/test';

const DOC010_ROUTES = [
  { logicalPath: '/', heading: 'Start' },
  { logicalPath: '/choose-your-path/', heading: 'Choose Your Path' },
  { logicalPath: '/spec-kit-lifecycle/', heading: 'Spec Kit Lifecycle' },
  { logicalPath: '/glossary/', heading: 'Glossary' },
  { logicalPath: '/reference/skills/', heading: 'Skills Reference' },
  { logicalPath: '/contribute-and-release/', heading: 'Contribute & Release' },
];

function routeUrl(logicalPath) {
  return logicalPath === '/' ? './' : `.${logicalPath}`;
}

test.describe('DOC-010 route smoke', () => {
  for (const route of DOC010_ROUTES) {
    test(`${route.logicalPath} loads the route heading`, async ({ page }) => {
      await page.goto(routeUrl(route.logicalPath));

      await expect(page.getByRole('main')).toBeVisible();
      await expect(page.getByRole('heading', { level: 1, name: route.heading })).toBeVisible();
    });
  }
});
