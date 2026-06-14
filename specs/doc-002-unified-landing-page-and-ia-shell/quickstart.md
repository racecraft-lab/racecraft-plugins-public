# Quickstart: DOC-002 docs-site shell

Use this guide after implementation creates `docs-site/`.

## Prerequisites

- `pnpm` available locally.
- Work from the repository root, then change into `docs-site/` for docs commands.
- Do not run or add a GitHub Pages publish workflow for DOC-002.

If `pnpm` is missing, stop setup, enable or install `pnpm` in the local
development environment, and rerun the docs-site install command. Do not switch
DOC-002 to root `npm`/`yarn` commands or a repository-wide workspace.

## Setup

```bash
cd docs-site
pnpm install
```

Expected outcome: `pnpm-lock.yaml` is present and dependencies install for the docs app only.

Reliability note: dependency installation may require package-registry network
access when the scaffold or lockfile is first created. After dependencies and
`pnpm-lock.yaml` are present, the repeatable DOC-002 completion gate is local to
`docs-site/`.

Failure next action: fix the docs-site package manifest, selected package
versions, registry access, or lockfile refresh, then rerun `pnpm install` from
`docs-site/`. Treat this as setup, not a reason to change frameworks.

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

Failure boundary: this blocks DOC-002 for Astro/Starlight config errors,
content/frontmatter/schema errors, route generation failures, invalid sidebar
slugs, or mismatched GitHub Pages `site`, `base`, or `trailingSlash` settings.
It is not a deployment check.

Failure next action: repair the failing docs-site config, package script,
content/frontmatter/schema, route file, sidebar slug, or Pages config value,
then rerun `pnpm build` and `pnpm validate`. Reopen the DOC-001 framework
fallback only if Astro/Starlight cannot satisfy GitHub Pages hosting,
MDX/component authoring, accessible static fallback, dependency policy, or
maintainability after local fixes are attempted or ruled out.

## Internal-Link Validation

```bash
cd docs-site
pnpm validate:links
```

Expected outcome: The Starlight link validator runs through the production build path and fails on broken internal Markdown/MDX route links.

Failure boundary: this blocks DOC-002 for invalid internal routes, anchors,
trailing slashes, or same-site/base-path link issues. External official-doc URL
availability and external-link crawling are outside the DOC-002 minimum gate.

Failure next action: fix the broken Markdown/MDX route link, heading anchor,
trailing-slash expectation, same-site URL, or base-path assumption in docs-site
content/config, then rerun `pnpm validate:links`. Do not add an external-link
crawler for DOC-002.

## Full DOC-002 Validation

```bash
cd docs-site
pnpm validate
```

Expected outcome: `pnpm check && pnpm build` passes, and internal-link validation runs as part of the build.

Minimum gate: after dependency setup, `pnpm check`, `pnpm build`,
`pnpm validate`, and `pnpm validate:links` must be rerunnable without GitHub
Pages deployment, browser screenshots, analytics checks, external-link crawling,
remote URL availability checks, or additional package-network access.

Pages mismatch next action: keep `site: "https://racecraft-lab.github.io"`,
`base: "/racecraft-plugins-public"`, and `trailingSlash: "always"` aligned with
Starlight route slugs and internal links, then rerun `pnpm build` and
`pnpm validate:links`. Do not add `.github/workflows/**`; DOC-010 owns the
publish workflow.

## Static Preview

```bash
cd docs-site
pnpm preview
```

Expected outcome: Astro serves the built site locally so a reviewer can inspect the landing page, sidebar groups, platform links, source-vs-payload explanation, and route shell metadata.

## Review Checks

- Landing page first screen states marketplace purpose, `speckit-pro`, Claude Code and Codex paths, source-vs-generated-payload distinction, and next actions.
- Landing page first screen stays within the FR-018 shell boundary: concise
  purpose/value, platform choices, source-vs-payload summary, and static next
  actions, without full install procedures or broad marketing content.
- Sidebar exposes Tutorials, How-to, Reference, and Explanation groups.
- All 11 route shells exist and display purpose, owner DOC, success criterion, and source evidence.
- Deferred route shells include audience, useful-now shell content, deferred
  owner DOC, source evidence, and one static next step or related route link.
- `/` and `/reference` explain `speckit-pro/` source versus `dist/claude/**` and `dist/codex/**` generated payloads.
- No `.github/workflows/**`, README source files, plugin behavior files, generated payloads, marketplace manifests, hooks, agents, or release automation files are changed.
