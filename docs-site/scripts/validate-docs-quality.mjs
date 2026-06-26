#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const REPO_ROOT = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));

export const DOC010_ROUTES = Object.freeze([
  {
    logicalPath: '/',
    sourcePath: 'docs-site/src/content/docs/index.mdx',
    title: 'Start',
  },
  {
    logicalPath: '/choose-your-path/',
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    title: 'Choose Your Path',
  },
  {
    logicalPath: '/spec-kit-lifecycle/',
    sourcePath: 'docs-site/src/content/docs/spec-kit-lifecycle.mdx',
    title: 'Spec Kit Lifecycle',
  },
  {
    logicalPath: '/glossary/',
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    title: 'Glossary',
  },
  {
    logicalPath: '/reference/skills/',
    sourcePath: 'docs-site/src/content/docs/reference/skills.md',
    title: 'Skills Reference',
  },
  {
    logicalPath: '/contribute-and-release/',
    sourcePath: 'docs-site/src/content/docs/contribute-and-release.md',
    title: 'Contribute & Release',
  },
]);

export const DOC010_SAFETY_BOUNDARIES = Object.freeze({
  allowedInputs: Object.freeze([
    'checked-in repository docs-site sources',
    'checked-in generated reference pages',
    'local Astro preview served from docs-site',
  ]),
  forbiddenInputs: Object.freeze([
    'user home directories',
    'browser profiles',
    'environment secrets',
    'user-supplied JSON',
    'local plugin cache files',
  ]),
  forbiddenActions: Object.freeze([
    'live plugin installs',
    'destructive cleanup',
    'browser-side local command execution',
    'analytics or production telemetry',
    'external marketplace navigation',
  ]),
});

const DOC010_FOUNDATION_FILES = Object.freeze([
  'docs-site/package.json',
  'docs-site/playwright.config.mjs',
  'docs-site/tests/docs-smoke.spec.mjs',
]);

// DOC-014 (C1) retargeted the robots assertion. The static
// `docs-site/public/robots.txt` (DOC-011's `Disallow: /`) was removed so it could
// not shadow the dynamic endpoint; the crawler-access policy now lives in the
// `robots.txt.ts` endpoint source, which this gate asserts (matching the
// source-reading style of the noindex-meta assertion below). The policy ALLOWS
// the citation + training tiers and the default crawler, advertises a Sitemap,
// and emits NO `Disallow: /` (the deliberate max-discoverability posture).
const DOC014_ROBOTS_ENDPOINT_PATH = 'docs-site/src/pages/robots.txt.ts';
const DOC014_ROBOTS_REQUIRED_AGENTS = Object.freeze([
  // Citation tier.
  'OAI-SearchBot',
  'ChatGPT-User',
  'Claude-SearchBot',
  'Claude-User',
  'PerplexityBot',
  'Perplexity-User',
  // Training tier (ALLOWED — the inverse of the sibling).
  'GPTBot',
  'Google-Extended',
  'CCBot',
  'anthropic-ai',
  'ClaudeBot',
]);

// DOC-011 (C10) — the staging noindex guard. KEPT INTACT by DOC-014; only the
// robots assertion above was retargeted. Do NOT weaken this.
const DOC011_ASTRO_CONFIG_PATH = 'docs-site/astro.config.mjs';
const DOC011_STAGING_ROBOTS_META_PATTERN =
  /head:\s*\[[\s\S]*tag:\s*['"]meta['"][\s\S]*attrs:\s*\{[\s\S]*name:\s*['"]robots['"][\s\S]*content:\s*['"]noindex,\s*nofollow['"][\s\S]*\}[\s\S]*\]/;

const REQUIRED_DOC010_VALIDATE_CHAIN = Object.freeze([
  'pnpm reference:check',
  'pnpm check',
  'pnpm validate:links',
  'pnpm validate:safe-aids',
  'pnpm validate:quality',
  'pnpm validate:smoke:preview',
]);

const SUPPORT_ANCHOR_INVENTORY = Object.freeze([
  {
    publicPath: '/racecraft-plugins-public/choose-your-path/',
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    anchors: Object.freeze([
      'route-shell',
      'static-selector-fallback',
      'support-link-map',
      'install-source-update-guidance',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/install/claude-code/',
    sourcePath: 'docs-site/src/content/docs/install/claude-code.md',
    anchors: Object.freeze([
      'install-decision',
      'source-payload-and-cache',
      'install-path-matrix',
      'verify-the-install',
      'stale-update-checkpoint',
      'install-safety',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/install/codex/',
    sourcePath: 'docs-site/src/content/docs/install/codex.md',
    anchors: Object.freeze([
      'install-decision',
      'source-payload-and-cache',
      'install-path-matrix',
      'register-custom-agents',
      'verify-the-install',
      'stale-update-checkpoint',
      'install-safety',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/troubleshooting/',
    sourcePath: 'docs-site/src/content/docs/troubleshooting.md',
    anchors: Object.freeze([
      'symptom-matrix',
      'read-only-inspection-boundary',
      'when-to-switch-pages',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/update-and-rollback/',
    sourcePath: 'docs-site/src/content/docs/update-and-rollback.md',
    anchors: Object.freeze([
      'recovery-cases',
      'case-notes',
      'stale-cache',
      'rollback-anchors',
      'where-to-go-next',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/glossary/',
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    anchors: Object.freeze([
      'marketplace',
      'payload',
      'source-tree',
      'skill',
      'agent',
      'hook',
      'cache',
      'constitution',
      'lifecycle',
      'generated-reference',
      'source-update-guidance',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/reference/',
    sourcePath: 'docs-site/src/content/docs/reference.md',
    anchors: Object.freeze([
      'generated-reference-subpages',
      'generated-page-boundary',
      'doc-008-support-handoffs',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/reference/skills/',
    sourcePath: 'docs-site/src/content/docs/reference/skills.md',
    anchors: Object.freeze([
      'page-summary',
      'records',
      'install',
      'speckit-autopilot',
      'speckit-status',
    ]),
  },
  {
    publicPath: '/racecraft-plugins-public/contribute-and-release/',
    sourcePath: 'docs-site/src/content/docs/contribute-and-release.md',
    anchors: Object.freeze([
      'source-of-truth',
      'change-type-matrix',
      'contributor-path',
      'maintainer-release-readiness',
      'version-fields',
      'release-automation',
      'current-pr-checks-behavior',
      'final-checklist',
    ]),
  },
]);

const REQUIRED_SUPPORT_LINKS = Object.freeze([
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/install/claude-code/#install-decision',
    label: 'Claude Code install decision deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/install/codex/#install-decision',
    label: 'Codex install decision deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/troubleshooting/#symptom-matrix',
    label: 'troubleshooting symptom matrix deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/glossary/#marketplace',
    label: 'marketplace glossary deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/glossary/#payload',
    label: 'payload glossary deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    href: '/racecraft-plugins-public/glossary/#source-tree',
    label: 'source tree glossary deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    href: '/racecraft-plugins-public/choose-your-path/#support-link-map',
    label: 'choose-your-path support link map deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    href: '/racecraft-plugins-public/reference/skills/#install',
    label: 'generated skills install reference deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    href: '/racecraft-plugins-public/contribute-and-release/#change-type-matrix',
    label: 'release workflow change matrix deep link',
  },
  {
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    href: '/racecraft-plugins-public/update-and-rollback/#recovery-cases',
    label: 'recovery cases deep link',
  },
]);

const SOURCE_UPDATE_GUIDANCE = Object.freeze([
  {
    sourcePath: 'docs-site/src/content/docs/choose-your-path.mdx',
    heading: 'Install Source Update Guidance',
    requiredSnippets: Object.freeze([
      'external platform',
      'Claude Code',
      'Codex',
      'source update',
      'docs-site/scripts/validate-docs-quality.mjs',
    ]),
  },
  {
    sourcePath: 'docs-site/src/content/docs/glossary.md',
    heading: 'Source Update Guidance',
    requiredSnippets: Object.freeze([
      'external platform',
      'Claude Code',
      'Codex',
      'source update',
      'docs-site/scripts/validate-docs-quality.mjs',
    ]),
  },
]);

const FORBIDDEN_SOURCE_PATTERNS = Object.freeze([
  { label: 'child process execution', pattern: /\bchild_process\b|\bexec(?:File)?\s*\(|\bspawn\s*\(/ },
  { label: 'browser local file reads', pattern: /\bFileReader\b|<input[^>]+type=["']file["']/i },
  { label: 'browser storage inspection', pattern: /\blocalStorage\b|\bsessionStorage\b|\bindexedDB\b/ },
  { label: 'analytics or telemetry', pattern: /\bsendBeacon\b|\banalytics\b|\btelemetry\b/i },
]);

function repoResolve(relativePath) {
  return path.join(REPO_ROOT, relativePath);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function normalizeSlugText(value) {
  return value
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/&/g, ' and ')
    .replace(/[^A-Za-z0-9 -]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

function collectAnchors(source) {
  const anchors = new Set();
  const slugCounts = new Map();

  for (const match of source.matchAll(/(?:^|\n)#{2,6}\s+(.+?)\s*(?:\{#([A-Za-z0-9_-]+)\})?\s*(?=\n|$)/g)) {
    const explicitId = match[2];
    const baseSlug = explicitId || normalizeSlugText(match[1]);
    if (!baseSlug) continue;

    const seenCount = slugCounts.get(baseSlug) || 0;
    slugCounts.set(baseSlug, seenCount + 1);
    anchors.add(seenCount === 0 ? baseSlug : `${baseSlug}-${seenCount}`);
  }

  for (const match of source.matchAll(/\sid=["']([^"']+)["']/g)) {
    anchors.add(match[1]);
  }

  return anchors;
}

function normalizeMarkdownHeadingText(value) {
  return value
    .replace(/\s+\{#[A-Za-z0-9_-]+\}\s*$/, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[`*_~]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function readRepoText(relativePath, diagnostics) {
  const absolutePath = repoResolve(relativePath);

  try {
    return fs.readFileSync(absolutePath, 'utf8');
  } catch (error) {
    const errorCode = typeof error?.code === 'string' ? error.code : 'READ_ERROR';
    diagnostics.push(`${relativePath}: missing or unreadable file (${errorCode}).`);
    return '';
  }
}

function assertRepoRelative(relativePath, diagnostics) {
  if (path.isAbsolute(relativePath) || relativePath.includes('..')) {
    diagnostics.push(`${relativePath}: DOC-010 validation paths must be repo-relative.`);
  }
}

function normalizeCommand(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function validateRouteSources(diagnostics) {
  for (const route of DOC010_ROUTES) {
    assertRepoRelative(route.sourcePath, diagnostics);

    const routeSource = readRepoText(route.sourcePath, diagnostics);
    const titlePattern = new RegExp(`title:\\s*["']?${escapeRegExp(route.title)}["']?`);

    if (routeSource && !titlePattern.test(routeSource)) {
      diagnostics.push(
        `${route.sourcePath}: ${route.logicalPath} must keep frontmatter title "${route.title}".`,
      );
    }
  }
}

function validateFoundationFiles(diagnostics) {
  for (const relativePath of DOC010_FOUNDATION_FILES) {
    assertRepoRelative(relativePath, diagnostics);

    const source = readRepoText(relativePath, diagnostics);
    for (const { label, pattern } of FORBIDDEN_SOURCE_PATTERNS) {
      if (pattern.test(source)) {
        diagnostics.push(`${relativePath}: DOC-010 validation must not include ${label}.`);
      }
    }
  }
}

function validateDocsCommandChain(diagnostics) {
  const packagePath = 'docs-site/package.json';
  assertRepoRelative(packagePath, diagnostics);

  const source = readRepoText(packagePath, diagnostics);
  if (!source) return;

  let packageJson;
  try {
    packageJson = JSON.parse(source);
  } catch (error) {
    diagnostics.push(`${packagePath}: unable to parse JSON for DOC-010 validation chain (${error.message}).`);
    return;
  }

  const scripts = packageJson.scripts || {};
  const expectedChain = REQUIRED_DOC010_VALIDATE_CHAIN.join(' && ');
  const actualChain = normalizeCommand(scripts.validate);
  const actualCommands = actualChain
    .split(/\s*&&\s*/)
    .map((command) => normalizeCommand(command))
    .filter(Boolean);

  if (
    actualCommands.length !== REQUIRED_DOC010_VALIDATE_CHAIN.length ||
    REQUIRED_DOC010_VALIDATE_CHAIN.some((expectedCommand, index) => actualCommands[index] !== expectedCommand)
  ) {
    diagnostics.push(
      `${packagePath}: scripts.validate must run the DOC-010 validation chain in order: ${expectedChain}.`,
    );
  }

  for (const requiredCommand of REQUIRED_DOC010_VALIDATE_CHAIN) {
    const scriptName = requiredCommand.replace(/^pnpm\s+/, '');
    if (!scripts[scriptName]) {
      diagnostics.push(`${packagePath}: missing focused DOC-010 script "${scriptName}" used by scripts.validate.`);
    }
  }
}

function validateStagingIndexingGuard(diagnostics) {
  // DOC-014 (C1) — assert the crawler-access policy in the robots.txt.ts endpoint
  // source: every citation + training agent ALLOWED, a default `User-agent: *`
  // ALLOWED, a Sitemap advertised, and NO `Disallow: /` anywhere (the inverse of
  // the sibling's training block). The static `public/robots.txt` is intentionally
  // gone, so reading it here would be a false failure.
  assertRepoRelative(DOC014_ROBOTS_ENDPOINT_PATH, diagnostics);
  const robotsEndpointSource = readRepoText(DOC014_ROBOTS_ENDPOINT_PATH, diagnostics);
  if (robotsEndpointSource) {
    // Strip line and block comments so the assertions evaluate the emitted policy
    // (the code), not explanatory prose — the docstring necessarily mentions the
    // sibling's "Disallow: /" and the crawler names, which would otherwise mask a
    // real regression in the directives the endpoint actually emits.
    const robotsCode = robotsEndpointSource
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/\/\/[^\n]*/g, '');

    if (/Disallow:\s*\//.test(robotsCode)) {
      diagnostics.push(
        `${DOC014_ROBOTS_ENDPOINT_PATH}: crawler-access policy must NOT emit "Disallow: /" (DOC-014 allows the citation and training tiers).`,
      );
    }
    if (!/Allow:\s*\//.test(robotsCode)) {
      diagnostics.push(
        `${DOC014_ROBOTS_ENDPOINT_PATH}: crawler-access policy must emit "Allow: /" for permitted crawlers.`,
      );
    }
    if (!/User-agent:\s*\*/.test(robotsCode)) {
      diagnostics.push(
        `${DOC014_ROBOTS_ENDPOINT_PATH}: crawler-access policy must include a default "User-agent: *" group.`,
      );
    }
    if (!/Sitemap:/.test(robotsCode)) {
      diagnostics.push(
        `${DOC014_ROBOTS_ENDPOINT_PATH}: crawler-access policy must advertise a "Sitemap:" location derived from site+base.`,
      );
    }
    for (const agent of DOC014_ROBOTS_REQUIRED_AGENTS) {
      if (!robotsCode.includes(agent)) {
        diagnostics.push(
          `${DOC014_ROBOTS_ENDPOINT_PATH}: crawler-access policy must name the allowed crawler "${agent}".`,
        );
      }
    }
  }

  // DOC-011 (C10) — noindex-meta guard, KEPT INTACT (only the robots assertion
  // above was retargeted by DOC-014). Do NOT weaken this.
  assertRepoRelative(DOC011_ASTRO_CONFIG_PATH, diagnostics);
  const astroConfigSource = readRepoText(DOC011_ASTRO_CONFIG_PATH, diagnostics);
  if (!DOC011_STAGING_ROBOTS_META_PATTERN.test(astroConfigSource)) {
    diagnostics.push(
      `${DOC011_ASTRO_CONFIG_PATH}: DOC-011 staging pages must keep the Starlight robots meta guard with content "noindex, nofollow".`,
    );
  }
}

function validateSupportAnchorInventory(diagnostics) {
  for (const page of SUPPORT_ANCHOR_INVENTORY) {
    assertRepoRelative(page.sourcePath, diagnostics);

    const source = readRepoText(page.sourcePath, diagnostics);
    if (!source) continue;

    const anchors = collectAnchors(source);
    for (const anchor of page.anchors) {
      if (!anchors.has(anchor)) {
        diagnostics.push(
          `${page.sourcePath}: missing stable support anchor "${anchor}" for ${page.publicPath}#${anchor}.`,
        );
      }
    }
  }
}

function validateSupportCrossLinks(diagnostics) {
  for (const link of REQUIRED_SUPPORT_LINKS) {
    assertRepoRelative(link.sourcePath, diagnostics);

    const source = readRepoText(link.sourcePath, diagnostics);
    if (source && !source.includes(link.href)) {
      diagnostics.push(`${link.sourcePath}: missing ${link.label}: ${link.href}.`);
    }
  }
}

function validateSourceUpdateGuidance(diagnostics) {
  for (const guidance of SOURCE_UPDATE_GUIDANCE) {
    assertRepoRelative(guidance.sourcePath, diagnostics);

    const source = readRepoText(guidance.sourcePath, diagnostics);
    if (!source) continue;

    const expectedHeading = normalizeMarkdownHeadingText(guidance.heading);
    const hasHeading = Array.from(source.matchAll(/^##\s+(.+)$/gm)).some(
      (match) => normalizeMarkdownHeadingText(match[1]) === expectedHeading,
    );
    if (!hasHeading) {
      diagnostics.push(
        `${guidance.sourcePath}: missing "${guidance.heading}" for DOC-010 external platform source-update guidance.`,
      );
    }

    const normalizedSource = source.toLowerCase();
    for (const snippet of guidance.requiredSnippets) {
      if (!normalizedSource.includes(snippet.toLowerCase())) {
        diagnostics.push(
          `${guidance.sourcePath}: source-update guidance must mention "${snippet}" for external platform claims.`,
        );
      }
    }
  }
}

function validateSafetyBoundaries(diagnostics) {
  for (const [group, entries] of Object.entries(DOC010_SAFETY_BOUNDARIES)) {
    if (entries.length === 0) {
      diagnostics.push(`docs-site/scripts/validate-docs-quality.mjs: ${group} must not be empty.`);
    }
  }
}

// DOC-014 (T025 / C9 / FR-010): every content page MUST carry a non-empty
// `description:` frontmatter line. Presence is enforced (not advisory), so a
// missing/empty description FAILS validation. DOC-015 later refreshes the prose.
const DOC014_CONTENT_DOCS_DIR = 'docs-site/src/content/docs';

function validateMetaDescriptions(diagnostics) {
  const docsDirAbs = repoResolve(DOC014_CONTENT_DOCS_DIR);
  let dirents;
  try {
    dirents = fs.readdirSync(docsDirAbs, { recursive: true, withFileTypes: true });
  } catch (error) {
    const code = typeof error?.code === 'string' ? error.code : 'READ_ERROR';
    diagnostics.push(
      `${DOC014_CONTENT_DOCS_DIR}: unable to enumerate content pages for description validation (${code}).`,
    );
    return;
  }

  const pages = dirents
    .filter((entry) => entry.isFile() && /\.(md|mdx)$/.test(entry.name))
    .map((entry) => path.relative(REPO_ROOT, path.join(entry.parentPath ?? entry.path, entry.name)))
    .sort();

  if (pages.length === 0) {
    diagnostics.push(`${DOC014_CONTENT_DOCS_DIR}: no content pages found for description validation.`);
    return;
  }

  for (const relativePath of pages) {
    const source = readRepoText(relativePath, diagnostics);
    if (!source) continue;

    const frontmatter = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!frontmatter) {
      diagnostics.push(`${relativePath}: missing frontmatter; DOC-014 (FR-010) requires a non-empty description.`);
      continue;
    }

    // Convention (intentional): every content page carries a non-empty, single-line
    // inline `description:` value. Starlight meta descriptions are short strings, so
    // a one-line scalar is the enforced norm here — multi-line folded/block scalars
    // are not used. This checks presence + non-emptiness of that inline value.
    const descLine = frontmatter[1].match(/^description:[ \t]*(.*)$/m);
    const value = descLine ? descLine[1].trim().replace(/^["']|["']$/g, '').trim() : '';
    if (!value) {
      diagnostics.push(
        `${relativePath}: missing or empty \`description:\` frontmatter (DOC-014 FR-010 requires one on every content page).`,
      );
    }
  }
}

export function validateDocsQuality() {
  const diagnostics = [];

  validateRouteSources(diagnostics);
  validateFoundationFiles(diagnostics);
  validateDocsCommandChain(diagnostics);
  validateStagingIndexingGuard(diagnostics);
  validateSupportAnchorInventory(diagnostics);
  validateSupportCrossLinks(diagnostics);
  validateSourceUpdateGuidance(diagnostics);
  validateSafetyBoundaries(diagnostics);
  validateMetaDescriptions(diagnostics);

  return diagnostics;
}

function main() {
  const diagnostics = validateDocsQuality();

  if (diagnostics.length > 0) {
    console.error('DOC-010 docs quality validation failed:');
    for (const diagnostic of diagnostics) {
      console.error(`- ${diagnostic}`);
    }
    process.exit(1);
  }

  console.log('DOC-010 docs quality validation passed.');
}

const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : '';
if (invokedPath === fileURLToPath(import.meta.url)) {
  main();
}
