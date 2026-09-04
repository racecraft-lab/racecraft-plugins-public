import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { join, resolve } from 'node:path';

const repoRoot = resolve(import.meta.dirname, '..', '..');
const galleryRoot = join(repoRoot, 'speckit-pro', 'artifact-gallery');
const manifest = JSON.parse(readFileSync(join(galleryRoot, 'manifest.json'), 'utf8'));
const oracle = JSON.parse(readFileSync(join(repoRoot, 'tests', 'speckit-pro', 'unit', 'fixtures', 'artifact-gallery', 'catalog.json'), 'utf8'));
const entries = new Map(manifest.templates.map((entry) => [entry.id, entry]));
const shipped = oracle.filter(([, status]) => status === 'shipped');
const exportPairs = shipped.flatMap(([id, , kinds]) => kinds.map((kind) => [id, kind]));
const EMPTY_CASES = [
  ['implementation-plan', 'prompt', null, 'No objection was recorded.'],
  ['visual-designs', 'prompt', null, 'Choose one option and enter a rationale before copying.'],
  ['component-variants', 'prompt', null, 'Choose one option and enter a rationale before copying.'],
  ['triage-board', 'markdown', '[data-field="title"]', 'empty_required_value'],
  ['feature-flags', 'markdown', '[data-flag-field="description"]', 'empty_required_value'],
  ['prompt-tuner', 'markdown', '#prompt-template', '"template": ""'],
];

function fileURL(identifier) {
  return pathToFileURL(join(galleryRoot, 'templates', `${identifier}.html`)).href;
}

function catalogFacts() {
  return oracle.map(([id, status, kinds]) => [id, status, kinds]);
}

async function installGuards(page, context) {
  const unexpected = [];
  await context.addInitScript(() => {
    Object.defineProperty(window, '__galleryCopies', { value: [] });
    Object.defineProperty(window, '__galleryClipboardMode', { value: 'resolve', writable: true });
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async (text) => {
        window.__galleryCopies.push(text);
        if (window.__galleryClipboardMode === 'reject') throw new DOMException('denied');
      } },
    });
  });
  await context.route(/^https?:\/\//, async (route) => {
    const url = route.request().url();
    if (!url.startsWith('https://fonts.googleapis.com/') && !url.startsWith('https://fonts.gstatic.com/')) unexpected.push(url);
    await route.abort();
  });
  page.on('worker', (worker) => unexpected.push(`worker:${worker.url()}`));
  page.on('websocket', (socket) => unexpected.push(`websocket:${socket.url()}`));
  page.on('popup', (popup) => unexpected.push(`popup:${popup.url()}`));
  page.on('framenavigated', (frame) => {
    if (frame === page.mainFrame() && !frame.url().startsWith('file:')) unexpected.push(`navigation:${frame.url()}`);
  });
  return unexpected;
}

async function load(page, identifier) {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(fileURL(identifier), { waitUntil: 'load' });
  await expect(page.locator('h1')).toHaveCount(1);
  await expect(page.locator('h1')).not.toBeEmpty();
  return errors;
}

async function scrollerFacts(page) {
  return page.locator('body *').evaluateAll((nodes) => nodes.map((element, index) => {
    const style = getComputedStyle(element);
    const box = element.getBoundingClientRect();
    const namedBy = element.getAttribute('aria-labelledby')?.split(/\s+/).map((id) => document.getElementById(id)?.textContent?.trim()).filter(Boolean).join(' ');
    return {
      index, role: element.getAttribute('role'), name: element.getAttribute('aria-label') || namedBy || '',
      overflow: ['auto', 'scroll'].includes(style.overflowX) && element.scrollWidth > element.clientWidth && box.width > 0 && box.height > 0 && !element.closest('details:not([open])'),
      className: typeof element.className === 'string' ? element.className : '',
    };
  }).filter((fact) => fact.overflow));
}

async function assertThemeAndScrollers(page, identifier) {
  const theme = page.getByRole('button', { name: 'Dark theme' });
  await expect(theme).toBeVisible();
  const beforeTheme = await page.locator('html').getAttribute('data-theme');
  await theme.click();
  await expect(page.locator('html')).not.toHaveAttribute('data-theme', beforeTheme);
  const seen = new Set();
  const classNames = new Set();
  const inspect = async () => {
    const regions = await scrollerFacts(page);
    for (const fact of regions) {
      if (seen.has(fact.index)) continue;
      seen.add(fact.index);
      classNames.add(fact.className);
      expect(fact.role).toBe('group');
      expect(fact.name.length).toBeGreaterThan(8);
      const region = page.locator('body *').nth(fact.index);
      const before = await region.evaluate((element) => { element.scrollLeft = 0; return element.scrollLeft; });
      await region.evaluate((element) => { element.focus(); });
      await expect.poll(() => region.evaluate((element) => document.activeElement === element), `${identifier}: ${fact.className || fact.role}`).toBe(true);
      await page.keyboard.press('ArrowRight');
      await expect.poll(() => region.evaluate((element) => element.scrollLeft)).toBeGreaterThan(before);
      await region.evaluate((element) => { element.scrollLeft = 0; });
    }
  };
  await inspect();
  const summaries = page.locator('details > summary');
  for (let index = 0; index < await summaries.count(); index += 1) {
    await summaries.nth(index).click();
    await inspect();
  }
  if (identifier === 'annotated-diff') expect([...classNames].some((name) => name.includes('diff'))).toBe(true);
  if (identifier === 'flowchart') expect([...classNames].some((name) => name.includes('diagram'))).toBe(true);
}

async function setLiveState(page, field, token) {
  const choice = page.locator('input[name^="chosen-"], input[name="chosen-base-variant"]').first();
  if (await choice.count()) await choice.check();
  const target = page.locator(field).first();
  const closed = target.locator('xpath=ancestor::details[not(@open)]').last().locator('summary');
  if (await closed.count()) await closed.click();
  await expect(target).toBeVisible();
  await target.fill(token);
}

function assertPayloadShape(payload, kind) {
  expect(payload.trim()).not.toBe('');
  expect(payload).toMatch(kind === 'prompt' ? /(?:Act on|Implement the)/ : /(?:recorded|chosen|Export kind: markdown)/i);
}

async function assertFallback(page, payload, status) {
  await expect.poll(() => status.innerText()).toMatch(/failed|could not/i);
  const fallback = page.locator('#fallback-field, #copy-fallback');
  await expect(fallback).toBeVisible();
  await expect(fallback).toBeFocused();
  expect(await fallback.inputValue()).toBe(payload);
  const id = await fallback.getAttribute('id');
  await expect(page.locator(`label[for="${id}"]`)).toBeVisible();
  await fallback.selectText();
  expect(await fallback.evaluate((element) => element.selectionEnd - element.selectionStart)).toBe(payload.length);
}

async function exerciseExport(page, row, kind, ordinal) {
  const [identifier, , kinds, , action, outcome, field] = row;
  const token = `gallery-${identifier}-${kind}-${ordinal}`;
  expect(kinds).toContain(kind);
  expect(action).toBe(`#copy-${kinds[0]}`);
  await setLiveState(page, field, token);
  const button = page.locator(`#copy-${kind}`);
  const status = page.locator(outcome);
  await expect(button).toHaveAttribute('type', 'button');
  await page.evaluate(() => { window.__galleryCopies.length = 0; window.__galleryClipboardMode = 'resolve'; });
  await button.click();
  await expect.poll(() => page.evaluate(() => window.__galleryCopies.length), `${identifier}/${kind}`).toBe(1);
  const [payload] = await page.evaluate(() => window.__galleryCopies);
  expect(payload).toContain(token);
  assertPayloadShape(payload, kind);
  await expect.poll(() => status.innerText()).not.toBe('');
  await expect(status).not.toContainText(/failed|could not/i);
  await page.evaluate(() => { window.__galleryClipboardMode = 'reject'; });
  await button.click();
  await assertFallback(page, payload, status);
}

test('frozen catalog keeps the manifest and 17 export pairs independently complete', () => {
  expect(oracle).toHaveLength(21);
  expect(shipped).toHaveLength(20);
  expect(oracle.filter(([, status]) => status === 'planned').map(([id]) => id)).toEqual(['uat-walkthrough']);
  expect(exportPairs).toHaveLength(17);
  expect(manifest.templates.map((entry) => [entry.id, entry.status, entry.exports])).toEqual(catalogFacts());
});

test('all shipped artifacts load offline, act, and expose every computed scroller', async ({ page, context }) => {
  const unexpected = await installGuards(page, context);
  await page.setViewportSize({ width: 360, height: 700 });
  for (const row of shipped) {
    const [identifier, , kinds, landmark, action, outcome] = row;
    const errors = await load(page, identifier);
    const entry = entries.get(identifier);
    expect(entry.title).toBeTruthy();
    expect(entry.stage).toBeTruthy();
    expect(entry.trigger).toBeTruthy();
    await expect(page.locator(landmark)).toHaveCount(1);
    if (!kinds.length && action) {
      const result = page.locator(outcome);
      const before = await result.innerText();
      await page.locator(action).click();
      await expect.poll(() => result.innerText()).not.toBe(before);
    }
    await assertThemeAndScrollers(page, identifier);
    expect(errors).toEqual([]);
  }
  expect(unexpected).toEqual([]);
});

test('every oracle export captures live state and has an exact failure fallback', async ({ page, context }) => {
  const unexpected = await installGuards(page, context);
  for (const [ordinal, [identifier, kind]] of exportPairs.entries()) {
    const row = shipped.find(([id]) => id === identifier);
    const errors = await load(page, identifier);
    await exerciseExport(page, row, kind, ordinal);
    expect(errors).toEqual([]);
  }
  expect(unexpected).toEqual([]);
});

test('each serialization family has an explicit blank-state outcome', async ({ page, context }) => {
  const unexpected = await installGuards(page, context);
  for (const [identifier, kind, field, expected] of EMPTY_CASES) {
    await load(page, identifier);
    if (field) await page.locator(field).first().fill('');
    await page.evaluate(() => { window.__galleryCopies.length = 0; window.__galleryClipboardMode = 'resolve'; });
    await page.locator(`#copy-${kind}`).click();
    const row = shipped.find(([id]) => id === identifier);
    const status = page.locator(row[5]);
    if (identifier === 'visual-designs' || identifier === 'component-variants') {
      await expect(status).toHaveText(expected);
      expect(await page.evaluate(() => window.__galleryCopies)).toEqual([]);
    } else {
      await expect.poll(() => page.evaluate(() => window.__galleryCopies.length)).toBe(1);
      expect((await page.evaluate(() => window.__galleryCopies))[0]).toContain(expected);
    }
  }
  expect(unexpected).toEqual([]);
});
