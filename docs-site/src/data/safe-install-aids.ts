// This module must stay plain JavaScript-compatible because the focused validator
// copies it to a temporary .mjs file before importing it in Node.
// @ts-nocheck
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pluginId = 'speckit-pro';
const sourceRelativeRoot = path.resolve(fileURLToPath(new URL('../../../', import.meta.url)));
const repoRootCandidates = [
  process.cwd(),
  path.resolve(process.cwd(), '..'),
  sourceRelativeRoot,
  path.resolve(sourceRelativeRoot, '..'),
];
const repoRoot =
  repoRootCandidates.find(
    (candidate) =>
      fs.existsSync(path.join(candidate, '.claude-plugin/marketplace.json')) &&
      fs.existsSync(path.join(candidate, 'speckit-pro/.claude-plugin/plugin.json')),
  ) ?? sourceRelativeRoot;
const siteBase = '/racecraft-plugins-public';

export const manifestSources = [
  {
    id: 'claude-marketplace',
    path: '.claude-plugin/marketplace.json',
    platform: 'claude-code',
    role: 'source-marketplace',
  },
  {
    id: 'codex-marketplace',
    path: '.agents/plugins/marketplace.json',
    platform: 'codex',
    role: 'source-marketplace',
  },
  {
    id: 'claude-source-plugin',
    path: 'speckit-pro/.claude-plugin/plugin.json',
    platform: 'claude-code',
    role: 'source-plugin',
  },
  {
    id: 'codex-source-plugin',
    path: 'speckit-pro/.codex-plugin/plugin.json',
    platform: 'codex',
    role: 'source-plugin',
  },
  {
    id: 'claude-dist-plugin',
    path: 'dist/claude/speckit-pro/.claude-plugin/plugin.json',
    platform: 'claude-code',
    role: 'dist-plugin',
  },
  {
    id: 'codex-dist-plugin',
    path: 'dist/codex/speckit-pro/.codex-plugin/plugin.json',
    platform: 'codex',
    role: 'dist-plugin',
  },
];

function sanitizeManifestError(relativePath, error) {
  if (error instanceof SyntaxError) return `INVALID_JSON: ${relativePath}`;
  if (error && typeof error === 'object' && 'code' in error && typeof error.code === 'string') {
    return `${error.code}: ${relativePath}`;
  }
  return `ERROR: ${relativePath}`;
}

function readManifest(relativePath) {
  try {
    const source = fs.readFileSync(path.join(repoRoot, relativePath), 'utf8');
    return {
      available: true,
      value: JSON.parse(source),
      error: '',
    };
  } catch (error) {
    return {
      available: false,
      value: null,
      error: sanitizeManifestError(relativePath, error),
    };
  }
}

const manifestInputs = Object.fromEntries(
  manifestSources.map((source) => [source.id, { ...source, ...readManifest(source.path) }]),
);

const manifestValue = (sourceId, getter) => {
  const source = manifestInputs[sourceId];
  if (!source?.available) return undefined;
  try {
    return getter(source.value);
  } catch {
    return undefined;
  }
};

const textValue = (value) => {
  if (value === undefined || value === null || value === '') return 'Unavailable';
  return String(value);
};

const marketplacePlugin = (manifest) => manifest.plugins?.find((plugin) => plugin?.name === pluginId);
const docsLink = (label, href) => ({ label, href: `${siteBase}${href}` });

export function compareManifestValues(leftValue, rightValue) {
  if (leftValue === undefined || leftValue === null || rightValue === undefined || rightValue === null) {
    return 'unavailable';
  }

  return String(leftValue) === String(rightValue) ? 'pass' : 'mismatch';
}

function comparison({
  id,
  label,
  rule,
  leftSource,
  rightSource,
  leftValue,
  rightValue,
  handoff,
  severity = 'pass',
  state,
}) {
  const computedState = state ?? compareManifestValues(leftValue, rightValue);
  return {
    id,
    label,
    rule,
    leftSource,
    rightSource,
    leftValue: textValue(leftValue),
    rightValue: textValue(rightValue),
    state: computedState,
    severity: computedState === 'pass' ? severity : 'caution',
    handoff,
  };
}

const pluginName = textValue(manifestValue('claude-source-plugin', (manifest) => manifest.name));
const pluginVersion = textValue(manifestValue('claude-source-plugin', (manifest) => manifest.version));
const claudeMarketplaceSource = textValue(manifestValue('claude-marketplace', (manifest) => marketplacePlugin(manifest)?.source));
const codexMarketplaceSource = textValue(manifestValue('codex-marketplace', (manifest) => marketplacePlugin(manifest)?.source?.path));

export const handoffs = [
  {
    id: 'claude-install',
    label: 'Claude Code install guide',
    href: `${siteBase}/install/claude-code/`,
    audience: 'installer',
    scope: 'Claude Code install orientation and stale-update checkpoints.',
  },
  {
    id: 'codex-install',
    label: 'Codex install guide',
    href: `${siteBase}/install/codex/`,
    audience: 'installer',
    scope: 'Codex marketplace, custom-agent registration, and restart orientation.',
  },
  {
    id: 'first-run',
    label: 'First-run checklist',
    href: `${siteBase}/first-run/`,
    audience: 'installer',
    scope: 'Safe workflow checkpoints before running local SpecKit workflows.',
  },
  {
    id: 'troubleshooting',
    label: 'Troubleshooting orientation',
    href: `${siteBase}/troubleshooting/`,
    audience: 'installer',
    scope: 'Lightweight handoff for mismatch, unavailable, cache, permission, or path questions. DOC-008 owns full diagnosis.',
  },
  {
    id: 'reference',
    label: 'Source and payload reference',
    href: `${siteBase}/reference/`,
    audience: 'evaluator',
    scope: 'Repository source, generated payload, and marketplace orientation.',
  },
  {
    id: 'contribute-release',
    label: 'Contribute and release',
    href: `${siteBase}/contribute-and-release/`,
    audience: 'maintainer',
    scope: 'Maintainer handoff when checked-in source or generated payload metadata must be refreshed.',
  },
];

export const selectorStateMessages = [
  {
    id: 'unsupported',
    label: 'Unsupported selector state',
    message:
      'This platform/scope pair is not one of the checked-in selector records. Keep using the supported static table below and follow the matching install guide.',
  },
  {
    id: 'unavailable',
    label: 'Unavailable selector metadata',
    message:
      'Selector metadata could not be read during docs generation. The supported static table remains the safe fallback, and the checker lists unavailable repository values.',
  },
  {
    id: 'ambiguous',
    label: 'Ambiguous selector state',
    message:
      'More than one selector record matched the same choice. Use the visible static path table and route maintainers to the source and payload reference.',
  },
];

export const selectorPaths = [
  {
    id: 'claude-marketplace-install',
    platform: 'claude-code',
    scope: 'Marketplace install',
    label: `Install ${pluginName} from the Racecraft Claude Code marketplace`,
    prerequisites: [
      'Claude Code can access the Racecraft marketplace source.',
      `The marketplace entry points at ${claudeMarketplaceSource}.`,
      'Managed settings allow plugin install and reload.',
    ],
    commands: [
      {
        id: 'claude-add-marketplace',
        platform: 'claude-code',
        label: 'Add the Racecraft marketplace',
        command: '/plugin marketplace add racecraft-lab/racecraft-plugins-public',
        expectedSignal: 'Claude Code adds the Racecraft marketplace source.',
        copyable: true,
      },
      {
        id: 'claude-install-plugin',
        platform: 'claude-code',
        label: 'Install the plugin',
        command: '/plugin install speckit-pro@racecraft-plugins-public',
        expectedSignal: `Claude Code installs ${pluginName} version ${pluginVersion}.`,
        copyable: true,
      },
      {
        id: 'claude-reload-plugin',
        platform: 'claude-code',
        label: 'Reload plugin surfaces',
        command: '/reload-plugins',
        expectedSignal: 'Claude Code reloads plugin skills, agents, hooks, and plugin UI surfaces.',
        copyable: true,
      },
      {
        id: 'claude-status-skill',
        platform: 'claude-code',
        label: 'Confirm the namespaced skill responds',
        command: '/speckit-pro:speckit-status',
        expectedSignal: 'The SpecKit Pro status skill responds from the installed plugin surface.',
        copyable: true,
      },
    ],
    successSignals: [
      'The Racecraft marketplace appears in Claude Code.',
      `${pluginName} appears as an installed plugin.`,
      '`/speckit-pro:speckit-status` responds after reload.',
    ],
    nextLinks: [
      docsLink('Open Claude Code install details', '/install/claude-code/'),
      docsLink('Start the first-run checklist', '/first-run/'),
    ],
    manifestRefs: ['.claude-plugin/marketplace.json', 'speckit-pro/.claude-plugin/plugin.json'],
  },
  {
    id: 'claude-repository-inspection',
    platform: 'claude-code',
    scope: 'Repository source inspection',
    label: 'Inspect Claude Code source and generated payload metadata',
    prerequisites: [
      'You need to compare repository source, marketplace, and generated Claude payload files before install or refresh.',
      'You are not using the browser page to edit installed runtime state.',
    ],
    commands: [
      {
        id: 'claude-open-plugin-view',
        platform: 'claude-code',
        label: 'Open installed plugin details',
        command: '/plugin',
        expectedSignal: 'Claude Code shows installed plugin details for observational comparison.',
        copyable: true,
      },
      {
        id: 'claude-refresh-marketplace',
        platform: 'claude-code',
        label: 'Refresh the marketplace when source changed',
        command: '/plugin marketplace update racecraft-plugins-public',
        expectedSignal: 'Claude Code refreshes the checked-in marketplace entry before reinstall or reload.',
        copyable: true,
      },
    ],
    successSignals: [
      'Marketplace source, source plugin manifest, and generated Claude payload version can be compared.',
      'Installed runtime state is treated as observation, not source of truth.',
    ],
    nextLinks: [
      docsLink('Review source and payload reference', '/reference/'),
      docsLink('Use troubleshooting orientation', '/troubleshooting/'),
    ],
    manifestRefs: ['dist/claude/speckit-pro/.claude-plugin/plugin.json'],
  },
  {
    id: 'codex-repo-marketplace',
    platform: 'codex',
    scope: 'Repo-scoped marketplace',
    label: `Install ${pluginName} from this repository in Codex`,
    prerequisites: [
      'This repository is open in Codex.',
      `The Codex marketplace entry points at ${codexMarketplaceSource}.`,
      'After plugin install, the Codex custom-agent registration skill still needs a local write approval.',
    ],
    commands: [
      {
        id: 'codex-open-plugin-browser',
        platform: 'codex',
        label: 'Open the Codex plugin browser',
        command: 'codex\n/plugins',
        expectedSignal: 'Codex shows the Racecraft Public Plugins marketplace and SpecKit Pro plugin card.',
        copyable: true,
      },
      {
        id: 'codex-install-agents',
        platform: 'codex',
        label: 'Run the Codex install skill',
        command: '@SpecKit Pro -> install\n$install',
        expectedSignal:
          'The install skill reports copied TOML filenames, the selected destination, and whether Codex must restart.',
        copyable: true,
      },
      {
        id: 'codex-status-skill',
        platform: 'codex',
        label: 'Confirm the Codex skill surface in a new thread',
        command: '$speckit-status',
        expectedSignal: 'A new Codex thread loads the SpecKit Pro skill surface.',
        copyable: true,
      },
    ],
    successSignals: [
      'SpecKit Pro is visible in Codex plugin surfaces.',
      'The install skill reports expected TOML files and restart guidance.',
      'A new thread can invoke `$speckit-*` skills.',
    ],
    nextLinks: [
      docsLink('Open Codex install details', '/install/codex/'),
      docsLink('Start the first-run checklist', '/first-run/'),
    ],
    manifestRefs: ['.agents/plugins/marketplace.json', 'speckit-pro/.codex-plugin/plugin.json'],
  },
  {
    id: 'codex-personal-local',
    platform: 'codex',
    scope: 'Personal or local payload',
    label: 'Point a personal Codex marketplace at a copied generated payload',
    prerequisites: [
      'You need SpecKit Pro outside this repository.',
      'The copied payload comes from `dist/codex/speckit-pro/`, not the mixed authoring source tree.',
      'The browser page remains copyable guidance only and never writes Codex configuration.',
    ],
    commands: [
      {
        id: 'codex-copy-payload',
        platform: 'codex',
        label: 'Sync the generated payload outside this page',
        command: 'cp -R dist/codex/speckit-pro ~/.codex/plugins/speckit-pro',
        expectedSignal: 'Your personal plugin location contains the generated Codex payload.',
        copyable: true,
      },
      {
        id: 'codex-personal-install',
        platform: 'codex',
        label: 'Install agents after plugin install',
        command: '@SpecKit Pro -> install\n$install',
        expectedSignal: 'The installer reports copied TOML files and restart guidance.',
        copyable: true,
      },
    ],
    successSignals: [
      'Personal marketplace points at a copied generated payload.',
      'Codex custom-agent TOML files are copied only after explicit local approval.',
    ],
    nextLinks: [
      docsLink('Review Codex install safety', '/install/codex/'),
      docsLink('Use source and payload reference', '/reference/'),
    ],
    manifestRefs: ['dist/codex/speckit-pro/.codex-plugin/plugin.json'],
  },
  {
    id: 'codex-cli-marketplace',
    platform: 'codex',
    scope: 'CLI marketplace add',
    label: 'Track a Codex marketplace source through the CLI',
    prerequisites: [
      'You know which local or Git-backed marketplace source Codex should track.',
      'Network access and approvals remain governed by Codex sandbox and approval policy.',
    ],
    commands: [
      {
        id: 'codex-cli-add-local',
        platform: 'codex',
        label: 'Add a local marketplace root',
        command: 'codex plugin marketplace add ./local-marketplace-root',
        expectedSignal: 'Codex records the local marketplace source.',
        copyable: true,
      },
      {
        id: 'codex-cli-add-git',
        platform: 'codex',
        label: 'Add a Git marketplace source',
        command: 'codex plugin marketplace add owner/repo --ref main',
        expectedSignal: 'Codex records the Git-backed marketplace source at the selected ref.',
        copyable: true,
      },
    ],
    successSignals: [
      'Codex tracks the selected marketplace source.',
      'The plugin card is available from the configured source before custom-agent registration.',
    ],
    nextLinks: [
      docsLink('Open Codex install details', '/install/codex/'),
      docsLink('Use troubleshooting orientation', '/troubleshooting/'),
    ],
    manifestRefs: ['.agents/plugins/marketplace.json'],
  },
];

export const checkerComparisons = [
  comparison({
    id: 'claude-name',
    label: 'Claude plugin name',
    rule: 'Claude source and generated payload plugin names must match.',
    leftSource: 'speckit-pro/.claude-plugin/plugin.json#/name',
    rightSource: 'dist/claude/speckit-pro/.claude-plugin/plugin.json#/name',
    leftValue: manifestValue('claude-source-plugin', (manifest) => manifest.name),
    rightValue: manifestValue('claude-dist-plugin', (manifest) => manifest.name),
    handoff: docsLink('Review source and payload reference', '/reference/'),
  }),
  comparison({
    id: 'claude-version',
    label: 'Claude plugin version',
    rule: 'Claude marketplace, source manifest, and generated payload versions must stay equal.',
    leftSource: `.claude-plugin/marketplace.json#/plugins[name=${pluginId}]/version`,
    rightSource: 'dist/claude/speckit-pro/.claude-plugin/plugin.json#/version',
    leftValue: manifestValue('claude-marketplace', (manifest) => marketplacePlugin(manifest)?.version),
    rightValue: manifestValue('claude-dist-plugin', (manifest) => manifest.version),
    handoff: docsLink('Use Claude stale update checkpoint', '/install/claude-code/'),
  }),
  comparison({
    id: 'codex-name',
    label: 'Codex plugin name',
    rule: 'Codex marketplace, source manifest, and generated payload plugin names must match.',
    leftSource: `.agents/plugins/marketplace.json#/plugins[name=${pluginId}]/name`,
    rightSource: 'dist/codex/speckit-pro/.codex-plugin/plugin.json#/name',
    leftValue: manifestValue('codex-marketplace', (manifest) => marketplacePlugin(manifest)?.name),
    rightValue: manifestValue('codex-dist-plugin', (manifest) => manifest.name),
    handoff: docsLink('Review source and payload reference', '/reference/'),
  }),
  comparison({
    id: 'codex-version',
    label: 'Codex plugin version',
    rule: 'Codex marketplace, source manifest, and generated payload versions must stay equal.',
    leftSource: `.agents/plugins/marketplace.json#/plugins[name=${pluginId}]/version`,
    rightSource: 'dist/codex/speckit-pro/.codex-plugin/plugin.json#/version',
    leftValue: manifestValue('codex-marketplace', (manifest) => marketplacePlugin(manifest)?.version),
    rightValue: manifestValue('codex-dist-plugin', (manifest) => manifest.version),
    handoff: docsLink('Use Codex stale update checkpoint', '/install/codex/'),
  }),
  comparison({
    id: 'claude-marketplace-source',
    label: 'Claude marketplace payload path',
    rule: 'Claude marketplace source must point at the generated Claude payload.',
    leftSource: `.claude-plugin/marketplace.json#/plugins[name=${pluginId}]/source`,
    rightSource: 'expected generated Claude payload path',
    leftValue: manifestValue('claude-marketplace', (manifest) => marketplacePlugin(manifest)?.source),
    rightValue: './dist/claude/speckit-pro',
    handoff: docsLink('Use maintainer release handoff', '/contribute-and-release/'),
  }),
  comparison({
    id: 'codex-marketplace-source',
    label: 'Codex marketplace payload path',
    rule: 'Codex marketplace source.path must point at the generated Codex payload.',
    leftSource: `.agents/plugins/marketplace.json#/plugins[name=${pluginId}]/source/path`,
    rightSource: 'expected generated Codex payload path',
    leftValue: manifestValue('codex-marketplace', (manifest) => marketplacePlugin(manifest)?.source?.path),
    rightValue: './dist/codex/speckit-pro',
    handoff: docsLink('Use maintainer release handoff', '/contribute-and-release/'),
  }),
  comparison({
    id: 'codex-skills-path-rewrite',
    label: 'Codex skills path rewrite',
    rule: 'Informational: source and generated Codex payloads intentionally use different skills paths.',
    leftSource: 'speckit-pro/.codex-plugin/plugin.json#/skills',
    rightSource: 'dist/codex/speckit-pro/.codex-plugin/plugin.json#/skills',
    leftValue: manifestValue('codex-source-plugin', (manifest) => manifest.skills),
    rightValue: manifestValue('codex-dist-plugin', (manifest) => manifest.skills),
    state: 'pass',
    severity: 'info',
    handoff: docsLink('Review source and payload reference', '/reference/'),
  }),
];

export const diagramNodes = [
  {
    id: 'source-tree',
    label: 'Source tree',
    kind: 'source-tree',
    description: '`speckit-pro/` contains mixed authoring source, source manifests, skills, agents, hooks, and docs inputs.',
    inputs: [],
    outputs: ['claude-dist', 'codex-dist', 'marketplace-entry'],
  },
  {
    id: 'claude-dist',
    label: 'Claude distribution',
    kind: 'claude-dist',
    description: '`dist/claude/speckit-pro/` is the generated Claude Code plugin payload referenced by the Claude marketplace.',
    inputs: ['source-tree'],
    outputs: ['marketplace-entry'],
  },
  {
    id: 'codex-dist',
    label: 'Codex distribution',
    kind: 'codex-dist',
    description: '`dist/codex/speckit-pro/` is the generated Codex plugin payload referenced by the Codex marketplace.',
    inputs: ['source-tree'],
    outputs: ['marketplace-entry', 'codex-cache'],
  },
  {
    id: 'marketplace-entry',
    label: 'Marketplace entries',
    kind: 'marketplace-entry',
    description: 'Repository marketplace JSON files point installers at the generated platform payloads, not at runtime cache state.',
    inputs: ['source-tree', 'claude-dist', 'codex-dist'],
    outputs: ['codex-cache'],
  },
  {
    id: 'codex-cache',
    label: 'Codex cache',
    kind: 'codex-cache',
    description: '`~/.codex/plugins/cache/...` is installed runtime state. Treat it as observation, not the editable source of truth.',
    inputs: ['marketplace-entry', 'codex-dist'],
    outputs: [],
  },
];

export const firstRunCheckpoints = [
  {
    id: 'platform-route',
    label: 'Platform install route',
    category: 'platform-route',
    description: 'Choose Claude Code or Codex before copying commands so platform-specific surfaces do not mix.',
    handoff: docsLink('Choose an install guide', '/choose-your-path/'),
  },
  {
    id: 'spec-kit-cli',
    label: 'Spec Kit CLI exists/version',
    category: 'prerequisite',
    description: 'Confirm the Spec Kit CLI is available before running local SpecKit workflows.',
    handoff: docsLink('Start the first run', '/first-run/'),
  },
  {
    id: 'constitution',
    label: 'Constitution available',
    category: 'repository-state',
    description: 'Confirm `.specify/memory/constitution.md` is present before relying on workflow gates.',
    handoff: docsLink('Review lifecycle gates', '/spec-kit-lifecycle/'),
  },
  {
    id: 'roadmap-spec-id',
    label: 'Roadmap or SPEC-ID selected',
    category: 'repository-state',
    description: 'Confirm the roadmap or SPEC-ID points at the intended feature before scaffolding.',
    handoff: docsLink('Review source reference', '/reference/'),
  },
  {
    id: 'github-cli',
    label: 'GitHub CLI',
    category: 'prerequisite',
    description: '`gh` is ready when the workflow needs PR, issue, or check evidence.',
    handoff: docsLink('First-run checkpoints', '/first-run/'),
  },
  {
    id: 'jq',
    label: 'jq',
    category: 'prerequisite',
    description: '`jq` is ready when helper scripts inspect JSON gate output.',
    handoff: docsLink('First-run checkpoints', '/first-run/'),
  },
  {
    id: 'branch-worktree',
    label: 'Branch or worktree clean-state review',
    category: 'repository-state',
    description: 'Confirm the active branch or worktree is the intended lane and user changes are not accidentally overwritten.',
    handoff: docsLink('First-run checkpoints', '/first-run/'),
  },
  {
    id: 'scaffold-output',
    label: 'Scaffold output artifacts',
    category: 'scaffold-output',
    description: 'Confirm workflow, design concept, spec directory, and SPEC-MOC artifacts exist before autopilot starts.',
    handoff: docsLink('Lifecycle explainer', '/spec-kit-lifecycle/'),
  },
  {
    id: 'docs-validation',
    label: 'Docs validation evidence',
    category: 'validation',
    description: 'Capture focused DOC-006 validation, docs-site validation, and link validation evidence before PR review.',
    handoff: docsLink('Contributor and release handoff', '/contribute-and-release/'),
  },
];

export const safeInstallAids = {
  selectorPaths,
  manifestSources,
  manifestInputs: Object.values(manifestInputs).map((source) => ({
    id: source.id,
    path: source.path,
    platform: source.platform,
    role: source.role,
    available: source.available,
    error: source.error,
  })),
  checkerComparisons,
  diagramNodes,
  firstRunCheckpoints,
  handoffs,
  selectorStateMessages,
};
