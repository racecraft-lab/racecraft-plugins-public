import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, passthroughImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';

// ─── DOC-014 (T021/C7) — git-accurate sitemap <lastmod> ──────────────────────
//
// The sitemap freshness signal MUST come from each page's real git commit date,
// never the build time (FR-017). We collect every page's date with a SINGLE bulk
// `git log` walk built ONCE and memoized (NOT one subprocess per page — the
// O(pages) slow path, withastro/astro#16803). This mirrors Starlight's own
// `getAllNewestCommitDate`, which likewise does one `git log --name-status` pass
// and never records a date for a file with no history.
//
// `child_process` here is within the docs-site safe-aids guard's allowed surface:
// neither validate-doc006-safe-aids.mjs nor validate-docs-quality.mjs scans
// astro.config.mjs (they scan the interactive component sources and the DOC-010
// foundation files), so this build-time git read does not trip those gates.

const DOCS_SITE_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(DOCS_SITE_DIR, '..');
const CONTENT_DIR_REL = 'docs-site/src/content/docs';
const CONTENT_DIR_ABS = path.join(REPO_ROOT, CONTENT_DIR_REL);
// Single source for the production origin: defineConfig() below consumes SITE/BASE,
// and the sitemap serialize helpers derive SITE_BASE from them. The DOC-012 launch
// flip is therefore a one-place change (update SITE/BASE) with the helpers kept in
// sync — there is no second hardcoded domain to drift out of step (FR-012).
const SITE = 'https://racecraft-lab.github.io';
const BASE = '/racecraft-plugins-public';
const SITE_BASE = `${SITE}${BASE}`;

/**
 * Convert a content file path (repo-relative or absolute) to its Starlight route
 * slug: strip the content-dir prefix and the `.md`/`.mdx` extension; `index` (or
 * a trailing `/index`) maps to the landing slug `''`.
 */
function contentPathToSlug(filePath) {
  const unix = filePath.replace(/\\/g, '/');
  const rel = unix.includes(`${CONTENT_DIR_REL}/`)
    ? unix.slice(unix.indexOf(`${CONTENT_DIR_REL}/`) + CONTENT_DIR_REL.length + 1)
    : unix;
  const noExt = rel.replace(/\.(md|mdx)$/, '');
  if (noExt === 'index') return '';
  if (noExt.endsWith('/index')) return noExt.slice(0, -'/index'.length);
  return noExt;
}

/** Map a sitemap entry `url` back to its route slug (inverse of pageUrl). */
function urlToSlug(url) {
  if (!url.startsWith(SITE_BASE)) return undefined;
  const tail = url.slice(SITE_BASE.length).replace(/^\/+/, '').replace(/\/+$/, '');
  return tail; // '' for the landing page.
}

/**
 * Build (once) a `slug -> ISO-8601 date` map from a single bulk `git log` walk
 * over the content dir. A file with no commit history gets NO entry (so its
 * `<lastmod>` is omitted downstream unless a frontmatter date pins it).
 */
let gitDateMapCache;
function gitDateMap() {
  if (gitDateMapCache) return gitDateMapCache;
  const map = new Map();
  let stdout = '';
  try {
    stdout = execFileSync(
      'git',
      ['log', '--format=t:%cI', '--name-status', '--', CONTENT_DIR_REL],
      { cwd: REPO_ROOT, encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 },
    );
  } catch {
    // No git history available (e.g. a tarball checkout). Leave the map empty;
    // every page then falls through to the frontmatter date or an omitted
    // <lastmod> — never the build time.
    gitDateMapCache = map;
    return map;
  }

  let runningDate;
  for (const line of stdout.split('\n')) {
    if (line.startsWith('t:')) {
      runningDate = line.slice(2).trim();
      continue;
    }
    const tab = line.lastIndexOf('\t');
    if (tab === -1) continue;
    const fileName = line.slice(tab + 1).trim(); // repo-relative path.
    if (!fileName.startsWith(`${CONTENT_DIR_REL}/`)) continue;
    if (!/\.(md|mdx)$/.test(fileName)) continue;
    const slug = contentPathToSlug(fileName);
    // The log is newest-first, so the FIRST date seen for a slug is the newest.
    if (runningDate && !map.has(slug)) map.set(slug, runningDate);
  }

  gitDateMapCache = map;
  return map;
}

/**
 * Read a per-page frontmatter date override (`lastUpdated:` or `date:`) for a
 * slug, if the page pins one. Returns an ISO-8601 string or undefined. This is
 * applied ON TOP of the git date map (FR-017: a page MAY pin its own date).
 */
function frontmatterDateForSlug(slug) {
  const candidates =
    slug === ''
      ? ['index.md', 'index.mdx']
      : [`${slug}.md`, `${slug}.mdx`, `${slug}/index.md`, `${slug}/index.mdx`];
  for (const candidate of candidates) {
    const abs = path.join(CONTENT_DIR_ABS, candidate);
    if (!fs.existsSync(abs)) continue;
    const text = fs.readFileSync(abs, 'utf-8');
    const fm = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!fm) return undefined;
    const match = fm[1].match(/^(?:lastUpdated|date):\s*(.+?)\s*$/m);
    if (!match) return undefined;
    const raw = match[1].replace(/^['"]|['"]$/g, '');
    const parsed = new Date(raw);
    return Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString();
  }
  return undefined;
}

/**
 * Resolve a sitemap entry's `<lastmod>` (FR-017 order):
 *   1. an explicit frontmatter `lastUpdated`/`date` if the page pins one;
 *   2. otherwise the page's git commit date from the bulk map;
 *   3. otherwise undefined — so @astrojs/sitemap OMITS <lastmod> (NEVER build time).
 */
function resolveLastmod(url) {
  const slug = urlToSlug(url);
  if (slug === undefined) return undefined;
  return frontmatterDateForSlug(slug) ?? gitDateMap().get(slug);
}

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: 'always',
  // DOC-013 — the brand logo/mark assets are SVG vectors that should be served
  // as-is; the passthrough image service avoids a Sharp rasterization dependency
  // that docs-site does not ship as a direct dependency.
  image: { service: passthroughImageService() },
  integrations: [
    starlight({
      title: 'Racecraft Public Plugins',
      plugins: [starlightLinksValidator(), starlightLlmsTxt()],
      customCss: ['./src/styles/brand.css'],
      // DOC-014 (D7) — visible "last updated" stamp from the git commit date,
      // consistent with the sitemap <lastmod> (frontmatter date override allowed).
      lastUpdated: true,
      // DOC-014 (D2) — route-data middleware is the single head-injection
      // mechanism (JSON-LD @graph + per-page OG/twitter tags); Starlight 0.40
      // designates a Head.astro override "a last resort".
      routeMiddleware: './src/routeData.ts',
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
    // DOC-014 (D6) — promote @astrojs/sitemap to a direct dep so we can attach a
    // custom serialize(). Starlight 0.40 defers to a user-provided @astrojs/sitemap,
    // so adding it directly does NOT raise a duplicate-instance error.
    //
    // NOTE: the integration's top-level `lastmod` option is intentionally NOT set —
    // a page with no git history must be able to OMIT <lastmod> entirely (the
    // sitemap protocol allows it), and the default top-level lastmod would be the
    // build time, which Google distrusts (FR-017).
    sitemap({
      // DOC-014 (T021/C7) — set each entry's <lastmod> from the page's real git
      // commit date via the single bulk `git log` walk above (memoized), honoring
      // a per-page frontmatter date override. A page with no commit history and no
      // pinned date gets its <lastmod> OMITTED (we leave `item.lastmod` undefined),
      // which @astrojs/sitemap renders as no <lastmod> element — NEVER build time.
      serialize(item) {
        const lastmod = resolveLastmod(item.url);
        if (lastmod) {
          item.lastmod = lastmod;
        } else {
          delete item.lastmod;
        }
        return item;
      },
    }),
  ],
});
