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

export function validateDocsQuality() {
  const diagnostics = [];

  validateRouteSources(diagnostics);
  validateFoundationFiles(diagnostics);
  validateSupportAnchorInventory(diagnostics);
  validateSupportCrossLinks(diagnostics);
  validateSourceUpdateGuidance(diagnostics);
  validateSafetyBoundaries(diagnostics);

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
