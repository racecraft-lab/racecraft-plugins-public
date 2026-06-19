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
