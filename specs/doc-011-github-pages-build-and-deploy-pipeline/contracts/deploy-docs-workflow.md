# Contract: DOC-011 Deploy Docs Workflow

## Workflow File

- Path: `.github/workflows/deploy-docs.yml`
- Name: `Deploy Docs`
- Automatic event: `push` to `main`
- Manual event: `workflow_dispatch`
- Environment: `github-pages`

## Required Permissions

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

No broader default token permissions are allowed for DOC-011 unless implementation finds a documented Pages Actions requirement that this contract does not cover.

## Required Path Filter Contract

The push trigger must use explicit `paths`, not `paths-ignore`. It must include broad docs-impacting source coverage and ordered fixture exclusions:

```yaml
on:
  push:
    branches: [main]
    paths:
      - ".github/workflows/deploy-docs.yml"
      - ".github/workflows/pr-checks.yml"
      - ".github/workflows/release.yml"
      - "docs-site/**"
      - "docs/prd-interactive-documentation.md"
      - "docs/roadmap-interactive-documentation.md"
      - ".specify/integrations/**"
      - ".claude-plugin/marketplace.json"
      - ".agents/plugins/marketplace.json"
      - "README.md"
      - "scripts/**"
      - "release-please-config.json"
      - ".release-please-manifest.json"
      - "speckit-pro/.claude-plugin/plugin.json"
      - "speckit-pro/.codex-plugin/plugin.json"
      - "speckit-pro/README.md"
      - "speckit-pro/**/README.md"
      - "speckit-pro/codex-hooks.json"
      - "speckit-pro/skills/**"
      - "speckit-pro/codex-skills/**"
      - "speckit-pro/agents/**"
      - "speckit-pro/codex-agents/**"
      - "speckit-pro/hooks/**"
      - "speckit-pro/scripts/**"
      - "tests/speckit-pro/**"
      - "!tests/speckit-pro/**/fixtures/**"
      - "!tests/speckit-pro/**/fixtures-codex/**"
      - "!tests/speckit-pro/layer7-integration/dispatch-fixtures/**"
      - "!tests/speckit-pro/layer7-integration/return-format-fixtures/**"
      - "!tests/speckit-pro/layer7-integration/e2e-fixtures/**"
      - "!tests/speckit-pro/layer7-integration/test-fixtures/**"
      - "!tests/speckit-pro/layer8-parity/**"
      - "dist/claude/speckit-pro/**"
      - "dist/codex/speckit-pro/**"
  workflow_dispatch:
```

The broad-path tradeoff is intentional: DOC-011 favors avoiding missed generated-reference deploys over minimizing every deploy run. Non-rendered process/archive state such as `docs/ai/specs/**`, `specs/**`, and `.specify/memory/**` remains excluded unless later identified as a docs-site or generated-reference input.

## Required Jobs

### Build And Upload Job

Required behavior:

1. Check out the repository.
2. Set up Node 22.
3. Enable Corepack and activate pnpm 10.25.0.
4. Install docs-site dependencies with `pnpm --dir docs-site install --frozen-lockfile`.
5. Install Chromium only with `pnpm --dir docs-site exec playwright install --with-deps chromium`.
6. Run `pnpm --dir docs-site validate`.
7. Configure Pages.
8. Upload `docs-site/dist` with `actions/upload-pages-artifact`.

### Deploy Job

Required behavior:

1. Depend on the build/upload job.
2. Deploy with `actions/deploy-pages`.
3. Use the `github-pages` environment.
4. Expose the deployed page URL from the Pages deploy step when GitHub provides it.

## Staging Indexing Contract

- `docs-site/astro.config.mjs` must add one Starlight `head` entry equivalent to `{ tag: 'meta', attrs: { name: 'robots', content: 'noindex, nofollow' } }`.
- `docs-site/public/robots.txt` must contain exactly:

```text
User-agent: *
Disallow: /
```

- The runbook must state that `robots.txt` is policy/signaling on a GitHub Pages project site, while the page-level noindex meta tag is the primary DOC-011 indexing guard.
- DOC-012 owns removal of this guard.
