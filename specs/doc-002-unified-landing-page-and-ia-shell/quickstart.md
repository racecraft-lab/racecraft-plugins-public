# Quickstart: DOC-002 docs-site shell

Use this guide after implementation creates `docs-site/`.

## Prerequisites

- `pnpm` available locally.
- Work from the repository root, then change into `docs-site/` for docs commands.
- Do not run or add a GitHub Pages publish workflow for DOC-002.

## Setup

```bash
cd docs-site
pnpm install
```

Expected outcome: `pnpm-lock.yaml` is present and dependencies install for the docs app only.

## Development Preview

```bash
cd docs-site
pnpm dev
```

Expected outcome: Astro starts a local Starlight development server and the 11 route shells are navigable through the sidebar.

## Production Build

```bash
cd docs-site
pnpm build
```

Expected outcome: Astro builds the static Starlight site successfully. No GitHub Pages workflow is created or required.

## Internal-Link Validation

```bash
cd docs-site
pnpm validate:links
```

Expected outcome: The Starlight link validator runs through the production build path and fails on broken internal Markdown/MDX route links.

## Full DOC-002 Validation

```bash
cd docs-site
pnpm validate
```

Expected outcome: `astro check && astro build` passes, and internal-link validation runs as part of the build.

## Static Preview

```bash
cd docs-site
pnpm preview
```

Expected outcome: Astro serves the built site locally so a reviewer can inspect the landing page, sidebar groups, platform links, source-vs-payload explanation, and route shell metadata.

## Review Checks

- Landing page first screen states marketplace purpose, `speckit-pro`, Claude Code and Codex paths, source-vs-generated-payload distinction, and next actions.
- Sidebar exposes Tutorials, How-to, Reference, and Explanation groups.
- All 11 route shells exist and display purpose, owner DOC, success criterion, and source evidence.
- `/` and `/reference` explain `speckit-pro/` source versus `dist/claude/**` and `dist/codex/**` generated payloads.
- No `.github/workflows/**`, README source files, plugin behavior files, generated payloads, marketplace manifests, hooks, agents, or release automation files are changed.
