#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repoRoot = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));
const routeMdx = path.join(repoRoot, 'docs-site/src/content/docs/choose-your-path.mdx');
const routeMd = path.join(repoRoot, 'docs-site/src/content/docs/choose-your-path.md');
const componentPath = path.join(repoRoot, 'docs-site/src/components/SafeInstallAids.astro');
const dataPath = path.join(repoRoot, 'docs-site/src/data/safe-install-aids.ts');

const requiredManifestPaths = [
  '.claude-plugin/marketplace.json',
  '.agents/plugins/marketplace.json',
  'speckit-pro/.claude-plugin/plugin.json',
  'speckit-pro/.codex-plugin/plugin.json',
  'dist/claude/speckit-pro/.claude-plugin/plugin.json',
  'dist/codex/speckit-pro/.codex-plugin/plugin.json',
];

const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

function readText(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    failures.push(`Missing or unreadable file: ${path.relative(repoRoot, filePath)} (${error.message})`);
    return '';
  }
}

function readJson(relativePath) {
  const fullPath = path.join(repoRoot, relativePath);
  try {
    return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  } catch (error) {
    failures.push(`Missing or invalid manifest JSON: ${relativePath} (${error.message})`);
    return null;
  }
}

function marketplacePlugin(manifest, relativePath) {
  const plugin = manifest?.plugins?.find((entry) => entry?.name === 'speckit-pro');
  assert(plugin, `${relativePath} must include a speckit-pro marketplace entry.`);
  return plugin;
}

async function loadDataModule() {
  if (!fs.existsSync(dataPath)) {
    failures.push('Missing data helper: docs-site/src/data/safe-install-aids.ts');
    return null;
  }

  const tempPath = path.join(path.dirname(dataPath), `.safe-install-aids.validate.${process.pid}.mjs`);
  fs.writeFileSync(tempPath, fs.readFileSync(dataPath, 'utf8'));

  try {
    return await import(`${pathToFileURL(tempPath).href}?cacheBust=${Date.now()}`);
  } catch (error) {
    failures.push(`Unable to import data helper as JavaScript-compatible TypeScript: ${error.message}`);
    return null;
  } finally {
    try {
      fs.unlinkSync(tempPath);
    } catch {
      // Best effort cleanup for the temporary validation import.
    }
  }
}

function validateRoute(routeSource) {
  assert(fs.existsSync(routeMdx), 'choose-your-path route must be converted to MDX.');
  assert(!fs.existsSync(routeMd), 'old choose-your-path.md source should not remain beside the MDX route.');
  assert(routeSource.includes('SafeInstallAids'), 'choose-your-path.mdx must import and render SafeInstallAids.');
  assert(routeSource.includes('title: "Choose Your Path"'), 'choose-your-path route frontmatter title must be preserved.');
}

function validateManifests() {
  const manifests = Object.fromEntries(requiredManifestPaths.map((manifestPath) => [manifestPath, readJson(manifestPath)]));
  const claudeMarketplace = marketplacePlugin(manifests['.claude-plugin/marketplace.json'], '.claude-plugin/marketplace.json');
  const codexMarketplace = marketplacePlugin(manifests['.agents/plugins/marketplace.json'], '.agents/plugins/marketplace.json');
  const claudeSource = manifests['speckit-pro/.claude-plugin/plugin.json'];
  const codexSource = manifests['speckit-pro/.codex-plugin/plugin.json'];
  const claudeDist = manifests['dist/claude/speckit-pro/.claude-plugin/plugin.json'];
  const codexDist = manifests['dist/codex/speckit-pro/.codex-plugin/plugin.json'];

  assert(claudeMarketplace?.name === claudeSource?.name, 'Claude marketplace plugin name must match Claude source manifest.');
  assert(claudeSource?.name === claudeDist?.name, 'Claude source plugin name must match Claude dist plugin name.');
  assert(codexMarketplace?.name === codexSource?.name, 'Codex marketplace plugin name must match Codex source manifest.');
  assert(codexSource?.name === codexDist?.name, 'Codex source plugin name must match Codex dist plugin name.');
  assert(claudeMarketplace?.version === claudeSource?.version, 'Claude marketplace version must match Claude source manifest.');
  assert(claudeSource?.version === claudeDist?.version, 'Claude source version must match Claude dist version.');
  assert(codexMarketplace?.version === codexSource?.version, 'Codex marketplace version must match Codex source manifest.');
  assert(codexSource?.version === codexDist?.version, 'Codex source version must match Codex dist version.');
  assert(claudeMarketplace?.source === './dist/claude/speckit-pro', 'Claude marketplace source must point to the generated Claude payload.');
  assert(codexMarketplace?.source?.path === './dist/codex/speckit-pro', 'Codex marketplace source.path must point to the generated Codex payload.');
}

function validateData(dataModule) {
  if (!dataModule?.safeInstallAids) return;

  const aids = dataModule.safeInstallAids;
  const selectorPaths = aids.selectorPaths ?? [];
  const checkerComparisons = aids.checkerComparisons ?? [];
  const diagramNodes = aids.diagramNodes ?? [];
  const checkpoints = aids.firstRunCheckpoints ?? [];
  const handoffs = aids.handoffs ?? [];

  assert(selectorPaths.length >= 4, 'selectorPaths must include multiple Claude Code and Codex paths.');
  assert(new Set(selectorPaths.map((item) => item.platform)).has('claude-code'), 'selectorPaths must include Claude Code.');
  assert(new Set(selectorPaths.map((item) => item.platform)).has('codex'), 'selectorPaths must include Codex.');

  for (const selectorPath of selectorPaths) {
    assert(selectorPath.id && selectorPath.platform && selectorPath.scope && selectorPath.label, `selectorPath ${selectorPath.id ?? '(missing id)'} is missing required identity fields.`);
    assert(selectorPath.prerequisites?.length > 0, `selectorPath ${selectorPath.id} must include prerequisites.`);
    assert(selectorPath.commands?.length > 0, `selectorPath ${selectorPath.id} must include commands.`);
    assert(selectorPath.successSignals?.length > 0, `selectorPath ${selectorPath.id} must include success signals.`);
    assert(selectorPath.nextLinks?.length > 0, `selectorPath ${selectorPath.id} must include next links.`);

    const commandText = selectorPath.commands.map((command) => command.command).join('\n');
    if (selectorPath.platform === 'claude-code') {
      assert(!commandText.includes('$speckit'), `Claude Code path ${selectorPath.id} must not render Codex $skill invocations.`);
      assert(!commandText.includes('@SpecKit Pro'), `Claude Code path ${selectorPath.id} must not render Codex plugin-card install guidance.`);
      assert(!commandText.includes('codex plugin'), `Claude Code path ${selectorPath.id} must not render Codex CLI marketplace guidance.`);
    }
    if (selectorPath.platform === 'codex') {
      assert(!commandText.includes('/plugin marketplace'), `Codex path ${selectorPath.id} must not render Claude /plugin marketplace guidance.`);
      assert(!commandText.includes('/reload-plugins'), `Codex path ${selectorPath.id} must not render Claude reload guidance.`);
      assert(!commandText.includes('/speckit-pro:'), `Codex path ${selectorPath.id} must not render Claude namespaced slash commands.`);
    }
  }

  const manifestSourcePaths = new Set((aids.manifestSources ?? []).map((source) => source.path));
  for (const manifestPath of requiredManifestPaths) {
    assert(manifestSourcePaths.has(manifestPath), `manifestSources must include ${manifestPath}.`);
  }

  assert(checkerComparisons.some((row) => row.state === 'pass' && row.severity === 'pass'), 'checkerComparisons must include passing repository consistency rows.');
  assert(checkerComparisons.some((row) => row.severity === 'info'), 'checkerComparisons must include informational packaging-difference rows.');
  for (const row of checkerComparisons) {
    assert(row.label && row.rule && row.leftSource && row.rightSource, `checker row ${row.id ?? '(missing id)'} is missing source/rule fields.`);
    assert('leftValue' in row && 'rightValue' in row, `checker row ${row.id} must expose compared values.`);
  }

  if (typeof dataModule.compareManifestValues === 'function') {
    assert(dataModule.compareManifestValues('2.14.3', '2.14.3') === 'pass', 'compareManifestValues must return pass for equal values.');
    assert(dataModule.compareManifestValues('2.14.3', '0.0.0') === 'mismatch', 'compareManifestValues must return mismatch for different values.');
    assert(dataModule.compareManifestValues('2.14.3', undefined) === 'unavailable', 'compareManifestValues must return unavailable for missing values.');
  } else {
    failures.push('data helper must export compareManifestValues for mismatch/unavailable fixture coverage.');
  }

  const diagramKinds = new Set(diagramNodes.map((node) => node.kind));
  for (const kind of ['source-tree', 'claude-dist', 'codex-dist', 'marketplace-entry', 'codex-cache']) {
    assert(diagramKinds.has(kind), `diagramNodes must include ${kind}.`);
  }

  const checkpointText = checkpoints.map((checkpoint) => `${checkpoint.label} ${checkpoint.description}`).join('\n').toLowerCase();
  for (const requiredText of ['platform', 'spec kit cli', 'constitution', 'roadmap', 'github cli', 'jq', 'branch', 'worktree', 'scaffold', 'docs validation']) {
    assert(checkpointText.includes(requiredText), `firstRunCheckpoints must cover ${requiredText}.`);
  }

  const handoffText = handoffs.map((handoff) => `${handoff.href} ${handoff.scope}`).join('\n');
  for (const requiredPath of ['/install/claude-code/', '/install/codex/', '/first-run/', '/troubleshooting/', '/reference/']) {
    assert(handoffText.includes(requiredPath), `handoffs must include ${requiredPath}.`);
  }

  const stateIds = new Set((dataModule.selectorStateMessages ?? []).map((state) => state.id));
  for (const state of ['unsupported', 'unavailable', 'ambiguous']) {
    assert(stateIds.has(state), `selectorStateMessages must include ${state}.`);
  }
}

function validateRenderingSources(routeSource, componentSource, dataSource) {
  assert(componentSource.includes('data-safe-install-aids'), 'SafeInstallAids component must expose a stable root data attribute.');
  assert(componentSource.includes('type=\"radio\"'), 'selector controls should use native radio inputs.');
  assert(componentSource.includes('data-path-panel'), 'component must render selected-path panels for progressive filtering.');
  assert(componentSource.includes('<table'), 'component must render semantic fallback/checker tables.');
  assert(componentSource.includes('<pre') && componentSource.includes('<code'), 'component must keep commands visible in code blocks.');
  assert(componentSource.includes('<li><pre><code>{command.command}</code></pre></li>'), 'static fallback command sequences must preserve line breaks.');
  assert(componentSource.includes('type=\"button\"') && componentSource.includes('navigator.clipboard'), 'copy affordance must use native buttons and clipboard copy only.');
  assert(componentSource.includes('aria-live'), 'selector or copy status must expose status text.');
  assert(componentSource.includes('Keyboard'), 'component must include keyboard/static-fallback review language.');
  assert(componentSource.includes("addEventListener('keydown'"), 'selector controls must handle keyboard navigation explicitly.');
  for (const key of ['ArrowDown', 'ArrowRight', 'Home', 'End']) {
    assert(componentSource.includes(key), `selector keyboard handler must support ${key}.`);
  }
  assert(componentSource.includes('.focus()'), 'selector keyboard handler must move focus with selection.');
  assert(componentSource.includes('grid-auto-rows: 1fr'), 'selector choice cards must keep equal row heights across breakpoints.');
  assert(componentSource.includes('align-items: stretch'), 'selector choice grid must stretch cards within equal-height tracks.');
  assert(componentSource.includes('box-sizing: border-box'), 'selector choice cards must include padding inside equal-height tracks.');
  assert(componentSource.includes('margin: 0'), 'selector choice cards must not inherit markdown flow margins.');

  const combined = `${routeSource}\n${componentSource}\n${dataSource}`;
  const forbiddenPatterns = [
    /child_process/,
    /\bexec\s*\(/,
    /\bspawn\s*\(/,
    /\beval\s*\(/,
    /FileReader/,
    /localStorage/,
    /contenteditable/i,
    /<textarea/i,
    /paste(?:d)? user json/i,
    /run[s]? shell commands from the browser/i,
  ];

  for (const pattern of forbiddenPatterns) {
    assert(!pattern.test(combined), `safe aid sources must not include unsafe browser/local diagnostic pattern: ${pattern}`);
  }

  assert(combined.includes('copyable guidance only'), 'sources must label commands as copyable guidance only.');
  assert(combined.includes('does not inspect local user files'), 'sources must state the checker does not inspect local user files.');
  assert(combined.includes('does not accept user JSON'), 'sources must state the checker does not accept user JSON.');
  assert(dataSource.includes('marketplacePlugin') && dataSource.includes(".find((plugin) => plugin?.name === pluginId)"), 'data helper must select marketplace entries by plugin name.');
  assert(dataSource.includes('sanitizeManifestError'), 'data helper must sanitize manifest read errors before rendering them.');
}

validateRoute(readText(routeMdx));
validateManifests();

const routeSource = readText(routeMdx);
const componentSource = readText(componentPath);
const dataSource = readText(dataPath);
const dataModule = await loadDataModule();

validateData(dataModule);
validateRenderingSources(routeSource, componentSource, dataSource);

if (failures.length > 0) {
  console.error('DOC-006 focused validation failed:');
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log('DOC-006 focused validation passed.');
