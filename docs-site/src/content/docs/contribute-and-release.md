---
title: "Contribute & Release"
description: "Move from a source edit to a release-ready pull request — how source files, generated payloads, marketplace registries, version fields, CI behavior, and release automation fit together."
---

Use this page when a maintainer or contributor needs to move from a source edit
to a release-ready PR. It separates source files from generated payloads,
marketplace registries, version fields, CI behavior, release automation, and PR
review evidence.

DOC-002 created this route shell. DOC-009 owns the full workflow content here.

## Source of Truth

| Area | Edit or review first | Generated or synchronized output | Deeper reference |
|------|----------------------|----------------------------------|------------------|
| Plugin source | `speckit-pro/` | `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/` | [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |
| Claude marketplace | `.claude-plugin/marketplace.json` | Version values synced from the Claude payload manifest under the marketplace entry's `source` path | [Manifests](/racecraft-plugins-public/reference/manifests/) |
| Codex marketplace | `.agents/plugins/marketplace.json` | Version values synced from the Codex payload manifest under the marketplace entry's `source.path` | [Manifests](/racecraft-plugins-public/reference/manifests/) |
| Payload scripts | `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh` | Generated payloads and marketplace version sync PRs | [Scripts](/racecraft-plugins-public/reference/scripts/) |
| Tests | `tests/speckit-pro/run-all.sh` | Deterministic release-readiness evidence | [Tests](/racecraft-plugins-public/reference/tests/) |
| Docs site | `docs-site/src/content/docs/` and `docs-site/package.json` | Static Astro/Starlight site output | [Reference overview](/racecraft-plugins-public/reference/) |
| Generated references | `docs-site/scripts/generate-reference-pages.mjs` | `docs-site/src/content/docs/reference/*.md` | [Reference overview](/racecraft-plugins-public/reference/) |

Primary sources: [CLAUDE.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md), [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json), [generate-reference-pages.mjs](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/scripts/generate-reference-pages.mjs), [build-plugin-payloads.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/build-plugin-payloads.sh), [sync-marketplace-versions.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/sync-marketplace-versions.sh), and [run-all.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.sh).

## Change Type Matrix

| Change type | Source surface | Generated or synchronized surface | Required evidence |
|-------------|----------------|-----------------------------------|-------------------|
| Docs-only, outside docs site | Markdown docs outside `docs-site/` | None by default | Explain changed docs and include any relevant source review evidence. |
| Docs-site content | `docs-site/src/content/docs/` | Astro/Starlight build output | `pnpm --dir docs-site validate`; use `reference:check` when generated references are involved. |
| Plugin source | `speckit-pro/` | `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/` | Payload rebuild evidence and `bash tests/speckit-pro/run-all.sh`. |
| Generated payload/dist | `scripts/build-plugin-payloads.sh` output or a release PR payload sync | `dist/**` | Explain the source change or release automation that generated the payloads. |
| Marketplace registry | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` | Version fields synced from platform plugin manifests | Marketplace sync evidence and manifest version consistency evidence. |
| Release automation | `.github/workflows/release.yml`, `release-please-config.json`, `.release-please-manifest.json` | Release PRs, GitHub Releases, payload/marketplace sync PRs | Release workflow rationale, PR Checks evidence, and rollback notes. |

For any mixed PR, combine the lanes. For example, a PR that changes plugin
source and docs-site content needs both plugin release-readiness evidence and
docs-site validation evidence.

Primary sources: [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml), [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), [release-please config](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/release-please-config.json), and [.release-please-manifest.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.release-please-manifest.json).

## Contributor Path

1. Classify the change with the matrix above.
2. Edit the smallest source surface that owns the behavior or content.
3. Do not hand-edit generated payloads, generated reference pages, or
   marketplace version fields unless the PR is specifically a generated sync.
4. Use a Conventional Commit PR title:
   `<type>(<optional scope>): <plain English description>`.
5. Write the PR body for a public reader. Include what changed, why it changed,
   non-goals, review order, validation evidence, known gaps, and rollback notes.
6. Include the validation commands that match the changed surfaces.

Good titles keep both pieces: the Conventional Commit prefix and plain English
after the colon. Avoid internal-only codes in the title or body.

Primary source: [CLAUDE.md PR title and body guidance](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md#contributing--branching-strategy).

## Maintainer Release Readiness

Use this command block as the consolidated release-readiness checklist. Run the
commands that match the PR surface and explain any skipped command in the PR
body.

```bash
bash scripts/build-plugin-payloads.sh
bash scripts/sync-marketplace-versions.sh
bash tests/speckit-pro/run-all.sh
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
```

What each command proves:

| Command | Use when | Evidence it provides |
|---------|----------|----------------------|
| `bash scripts/build-plugin-payloads.sh` | Plugin source or release payloads changed | Rebuilds isolated Claude and Codex install payloads under `dist/`. |
| `bash scripts/sync-marketplace-versions.sh` | Marketplace versions or release sync are in scope | Syncs marketplace entry versions from platform plugin manifests. |
| `bash tests/speckit-pro/run-all.sh` | Release readiness, especially plugin or release-affecting work | Runs the default deterministic shell suite. |
| `pnpm --dir docs-site reference:check` | Generated reference drift is possible | Verifies generated reference pages match the generator. |
| `pnpm --dir docs-site validate` | Any `docs-site/**` file changed | Runs `reference:check`, `astro check`, and `astro build` through the docs-site script chain. |

`pnpm --dir docs-site validate` is required for changes under `docs-site/**`.
Non-site Markdown changes do not automatically require docs-site validation, but
they still need reviewable evidence that matches the PR scope.

Primary sources: [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json), [build-plugin-payloads.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/build-plugin-payloads.sh), [sync-marketplace-versions.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/sync-marketplace-versions.sh), and [tests/speckit-pro/run-all.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.sh).

## Version Fields

Treat version fields as owned by their source hierarchy:

- Release-please owns release version bumps for
  `speckit-pro/.claude-plugin/plugin.json` and
  `speckit-pro/.codex-plugin/plugin.json`.
- Generated payload manifests under `dist/` are rebuilt from source by
  `bash scripts/build-plugin-payloads.sh`.
- Marketplace registry versions are synchronized from platform plugin manifests
  by `bash scripts/sync-marketplace-versions.sh`.
- Manual version edits should be rare and explicitly explained, such as a
  maintainer-approved release recovery.

Primary sources: [release-please-config.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/release-please-config.json), [.release-please-manifest.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.release-please-manifest.json), [Claude plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.claude-plugin/plugin.json), [Codex plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.codex-plugin/plugin.json), [Claude marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.claude-plugin/marketplace.json), and [Codex marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.agents/plugins/marketplace.json).

## Release Automation

The maintainer-facing release flow is:

1. A push to `main`, typically from a squash merge, triggers the Release
   workflow.
2. Release-please opens or updates a release PR when releasable Conventional
   Commits exist.
3. When release PRs are created, the Release workflow checks out the release PR
   branch, runs `bash scripts/build-plugin-payloads.sh`, commits `dist/**`
   payload updates back to that branch when needed, and manually dispatches
   `PR Checks`.
4. When a release PR is merged, release-please publishes the GitHub Release.
5. After release publication, the Release workflow rebuilds payloads, runs
   `bash scripts/sync-marketplace-versions.sh`, and opens or updates a
   `chore: sync plugin payloads and marketplace versions` PR when generated
   payloads or marketplace files changed.

The manual `PR Checks` dispatch is observable repository behavior. If you
explain the GitHub-token reason, scope it to this repository's workflow comments
and GitHub's recursion guard behavior rather than treating it as a general
platform rule for every event.

Primary sources: [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml) and [CLAUDE.md release process](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md#release-process).

## Current PR Checks Behavior

`PR Checks` runs on non-draft pull requests and can also be dispatched manually
by the Release workflow for release-please PR branches.

Current behavior to account for in review:

- The `detect` job compares changed files against the base branch.
- Plugin test matrix jobs run only when plugin-affecting paths changed, such as
  the plugin source directory, `tests/<plugin>/`, `dist/claude/<plugin>/`,
  `dist/codex/<plugin>/`, marketplace registries, packaging scripts,
  release-please config, or PR/release workflow files.
- Docs-only PRs with no plugin-affecting paths skip the plugin test matrix.
- `validate-plugins` still runs as the stable sentinel and passes when plugin
  tests passed or were skipped.
- `validate-pr-title` still checks the PR title against the split workflow and
  Conventional Commit contract.

Do not describe this as docs-site CI hardening. DOC-009 documents the current
PR Checks behavior and local docs-site validation expectations. DOC-010 owns
future CI hardening for site build, Markdown/link validation, search,
accessibility, deep links, responsive checks, manifest/payload consistency, and
safe command-snippet validation.

Primary source: [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml).

## Final Checklist

Before requesting review, confirm:

- The PR edits the smallest source surface that owns the change.
- Generated payload or generated reference changes are explained by their
  generator or sync contract.
- Source/dist parity is checked when plugin source or payloads are in scope.
- Claude and Codex marketplace parity is checked when marketplace files are in
  scope.
- Source plugin manifest versions, generated payload manifest versions, and
  marketplace versions are consistent with the release/version ownership model.
- `bash scripts/build-plugin-payloads.sh` ran or was not applicable.
- `bash scripts/sync-marketplace-versions.sh` ran or was not applicable.
- `bash tests/speckit-pro/run-all.sh` ran for release readiness or the PR body
  explains why it was not needed.
- `pnpm --dir docs-site validate` ran for any `docs-site/**` change.
- The PR title uses Conventional Commit format and plain English.
- The PR body is public-readable and includes validation evidence, known gaps,
  and rollback notes.
- DOC-010 remains the owner for future docs-site CI/search/accessibility/deep-link
  hardening.

Primary sources: [CLAUDE.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md), [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml), [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), and [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json).
