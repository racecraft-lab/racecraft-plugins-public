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
| Repo-local Python gates | `speckit-pro/speckit_pro_runner/` and `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/*.json` | Deterministic release-readiness, payload-evidence, install-verification, and active-path guard evidence | [Tests](/racecraft-plugins-public/reference/tests/) |
| Retained parity scripts | `scripts/*.sh`, `tests/speckit-pro/**/*.sh` | Inactive parity evidence until XPLAT-008 cutover | [Scripts](/racecraft-plugins-public/reference/scripts/) |
| Docs site | `docs-site/src/content/docs/` and `docs-site/package.json` | Static Astro/Starlight site output | [Reference overview](/racecraft-plugins-public/reference/) |
| Generated references | `docs-site/scripts/generate-reference-pages.mjs` | `docs-site/src/content/docs/reference/*.md` | [Reference overview](/racecraft-plugins-public/reference/) |

Primary sources: [CLAUDE.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md), [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json), [generate-reference-pages.mjs](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/scripts/generate-reference-pages.mjs), [build-plugin-payloads.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/build-plugin-payloads.sh), [sync-marketplace-versions.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/sync-marketplace-versions.sh), and [run-all.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.sh).

## Change Type Matrix

| Change type | Source surface | Generated or synchronized surface | Required evidence |
|-------------|----------------|-----------------------------------|-------------------|
| Docs-only, outside docs site | Markdown docs outside `docs-site/` | None by default | Explain changed docs and include any relevant source review evidence. |
| Docs-site content | `docs-site/src/content/docs/` | Astro/Starlight build output | `pnpm --dir docs-site validate`; use `reference:check` when generated references are involved. |
| Plugin source | `speckit-pro/` | `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/` | Python runner release-readiness evidence. |
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
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/active-path-guard.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/test-payload-evidence.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
```

What each command proves:

| Command | Use when | Evidence it provides |
|---------|----------|----------------------|
| `run-toolchain-preflight.json` | Before deterministic runner validation or when tool versions are in question | Reports Python runner prerequisites and source metadata readiness. |
| `run-default-suite.json` | Release readiness, especially plugin or release-affecting work | Runs the default deterministic Python runner suite gate. |
| `active-path-guard.json` | Any gate, workflow, helper, or release-readiness path changed | Proves active repo-local gates do not depend on Bash, `.sh`, `jq`, shell parsing, or shell interpolation. |
| `test-payload-evidence.json` | Payload evidence changed | Builds fixture-bound Claude/Codex test payload evidence only; generated release payload cutover remains XPLAT-008. |
| `install-verification.json` | Install inventory or local fixture behavior changed | Verifies fake-home install completeness and safe repair plans without mutating real installed caches. |
| `release-readiness.json` | Release, marketplace, workflow, payload, or PR-title checks are in scope | Aggregates fixture-bound release-readiness evidence and XPLAT-008 handoff items. |
| `pnpm --dir docs-site reference:check` | Generated reference drift is possible | Verifies generated reference pages match the generator. |
| `pnpm --dir docs-site validate` | Any `docs-site/**` file changed | Runs `reference:check`, `astro check`, and `astro build` through the docs-site script chain. |

`pnpm --dir docs-site validate` is required for changes under `docs-site/**`.
Non-site Markdown changes do not automatically require docs-site validation, but
they still need reviewable evidence that matches the PR scope.

Maintainer validation has two toolchain buckets:

| Bucket | Required tools |
|---|---|
| Deterministic plugin suite | Python 3.11+ and `git`; retained Bash/`jq` scripts are parity evidence, not XPLAT-007 active repo-local gates. |
| Docs-site validation | Node 22 or newer, Corepack, `pnpm@10.25.0`, installed `docs-site` dependencies, and Playwright for smoke validation. |

PR Checks dispatch the Python runner toolchain and default-suite gates on the
GitHub-hosted runner toolchain. Public release payload cutover, installed-cache
UAT, native platform UAT, update, autoheal, public release notes, and public
release-readiness claims remain XPLAT-008 work.

Live, AI-backed, or PR-backed validation can additionally require authenticated
`gh`, `specify`, `claude`, `codex`, the skill-creator plugin, and
`timeout`/`gtimeout` depending on the layer.

Primary sources: [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json), [build-plugin-payloads.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/build-plugin-payloads.sh), [sync-marketplace-versions.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/sync-marketplace-versions.sh), and [tests/speckit-pro/run-all.sh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.sh).

## Version Fields

Treat version fields as owned by their source hierarchy:

- Release-please owns release version bumps for
  `speckit-pro/.claude-plugin/plugin.json` and
  `speckit-pro/.codex-plugin/plugin.json`.
- Generated payload manifests under `dist/` remain XPLAT-008 public cutover
  work; XPLAT-007 runner gates build fixture-bound test payload evidence only.
- Marketplace registry version sync remains governed by release-readiness
  evidence until XPLAT-008 promotes public release payload cutover.
- Manual version edits should be rare and explicitly explained, such as a
  maintainer-approved release recovery.

Primary sources: [release-please-config.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/release-please-config.json), [.release-please-manifest.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.release-please-manifest.json), [Claude plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.claude-plugin/plugin.json), [Codex plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.codex-plugin/plugin.json), [Claude marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.claude-plugin/marketplace.json), and [Codex marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.agents/plugins/marketplace.json).

## Release Automation

The maintainer-facing release flow is:

1. A push to `main`, typically from a squash merge, triggers the Release
   workflow.
2. Release-please opens or updates a release PR when releasable Conventional
   Commits exist.
3. During XPLAT-007, release workflow validation dispatches Python runner
   release-readiness and payload-evidence gates. Generated release payloads,
   public release notes, update, autoheal, installed-cache UAT, and native
   platform UAT remain XPLAT-008 handoff items.
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

- The `detect` job emits the current speckit-pro plugin matrix for runner-gate
  validation.
- Plugin test matrix jobs dispatch Python runner gates instead of Bash or `jq`
  plugin validation logic.
- `validate-plugins` still runs as the stable sentinel and passes only when the
  plugin test matrix passed or was skipped.
- `validate-pr-title` dispatches runner release-readiness evidence during
  XPLAT-007; full active PR-title cutover remains bounded by XPLAT-008 release
  readiness.

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
- Python runner payload-evidence and release-readiness gates ran or were not
  applicable.
- Python runner default-suite and active-path guard gates ran for release
  readiness or the PR body explains why they were not needed.
- `pnpm --dir docs-site validate` ran for any `docs-site/**` change.
- The PR title uses Conventional Commit format and plain English.
- The PR body is public-readable and includes validation evidence, known gaps,
  and rollback notes.
- DOC-010 remains the owner for future docs-site CI/search/accessibility/deep-link
  hardening.

Primary sources: [CLAUDE.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/CLAUDE.md), [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml), [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), and [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json).
