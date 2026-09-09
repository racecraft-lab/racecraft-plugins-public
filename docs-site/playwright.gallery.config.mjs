import { defineConfig, devices } from '@playwright/test';
import os from 'node:os';
import path from 'node:path';

export default defineConfig({
  testDir: './tests',
  testMatch: 'artifact-gallery.spec.mjs',
  workers: 1,
  timeout: 30_000,
  outputDir: path.join(os.tmpdir(), 'racecraft-artifact-gallery-playwright'),
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 900 },
    serviceWorkers: 'block',
    screenshot: 'off',
    trace: 'off',
    video: 'off',
  },
  projects: [{ name: 'gallery-chromium' }],
});
