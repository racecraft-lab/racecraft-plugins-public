---
title: "Contribute & Release"
description: "Move from a source edit to a release-ready pull request — how source files, generated payloads, marketplace registries, version fields, CI behavior, and release automation fit together."
---

Use this page when a maintainer or contributor needs to move from a source edit
to a release-ready PR. It separates source files from generated payloads,
marketplace registries, version fields, CI behavior, release automation, and PR
review evidence.

## Source of Truth

| Area | Edit or review first | Generated or synchronized output | Deeper reference |
|------|----------------------|----------------------------------|------------------|
| Plugin source | `speckit-pro/` | `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/` | [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |
| Claude marketplace | `.claude-plugin/marketplace.json` | Version values synced from the Claude payload manifest under the marketplace entry's `source` path | [Manifests](/racecraft-plugins-public/reference/manifests/) |
| Codex marketplace | `.agents/plugins/marketplace.json` | Version values synced from the Codex payload manifest under the marketplace entry's `source.path` | [Manifests](/racecraft-plugins-public/reference/manifests/) |
| Payload and release tools | `speckit-pro/speckit_pro_runner/`, `scripts/refresh-release-artifacts.py`, `scripts/sync_release_pr.py`, `scripts/compose-release-notes.py` | Generated payloads, release-PR synchronization, and public release notes | [Scripts](/racecraft-plugins-public/reference/scripts/) |
| Tests | `tests/speckit-pro/suite-manifest.json`, `tests/speckit-pro/run-all.py`, `tests/speckit-pro/check-toolchain.py`, `tests/speckit-pro/unit/` | Manifest-driven deterministic and optional-layer evidence | [Tests](/racecraft-plugins-public/reference/tests/) |
| Docs site | `docs-site/src/content/docs/` and `docs-site/package.json` | Static Astro/Starlight site output | [Reference overview](/racecraft-plugins-public/reference/) |
| Generated references | `docs-site/scripts/generate-reference-pages.mjs` | `docs-site/src/content/docs/reference/*.md` | [Reference overview](/racecraft-plugins-public/reference/) |

Primary sources: [suite manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/suite-manifest.json), [unit tests](https://github.com/racecraft-lab/racecraft-plugins-public/tree/main/tests/speckit-pro/unit), [run-all.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.py), [check-toolchain.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/check-toolchain.py), [refresh-release-artifacts.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/refresh-release-artifacts.py), [compose-release-notes.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/compose-release-notes.py), and [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json).

## Change Type Matrix

| Change type | Source surface | Generated or synchronized surface | Required evidence |
|-------------|----------------|-----------------------------------|-------------------|
| Docs-only, outside docs site | Markdown docs outside `docs-site/` | None by default | Explain changed docs and include any relevant source review evidence. |
| Docs-site content | `docs-site/src/content/docs/` | Astro/Starlight build output | `pnpm --dir docs-site validate`; use `reference:check` when generated references are involved. |
| Plugin source | `speckit-pro/` | `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` | Generated-artifact consistency and `python3 tests/speckit-pro/run-all.py`. |
| Generated payload/dist | `scripts/refresh-release-artifacts.py` or the Release workflow's release-PR sync | `dist/**` | Explain the source change or workflow run that generated the outputs. |
| Marketplace registry | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` | Claude resolves the git commit because its manifest and marketplace entry intentionally omit `version`; release-please bumps the Codex version and artifact refresh synchronizes it | Cache-identity, manifest-version, and generated-artifact evidence. |
| Release automation | `.github/workflows/release.yml`, `scripts/sync_release_pr.py`, `scripts/compose-release-notes.py`, `release-please-config.json` | Release PRs, synchronized release artifacts, immutable release-input snapshots, GitHub Releases, and release-note audits | Workflow rationale, PR Checks evidence, snapshot/composer contract evidence, and rollback notes. |

For any mixed PR, combine the lanes. For example, a PR that changes plugin
source and docs-site content needs both plugin release-readiness evidence and
docs-site validation evidence.

Primary sources: [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml), [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), [release-please config](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/release-please-config.json), and [.release-please-manifest.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.release-please-manifest.json).

## Contributor Path

1. Classify the change with the matrix above.
2. Edit the smallest source surface that owns the behavior or content.
3. Do not hand-edit generated payloads, generated reference pages, or
   marketplace version fields unless the PR is specifically a generated sync.
4. Use a scoped Conventional Commit PR title:
   `<type>(<lowercase scope>): <plain English description>`. The live title
   gate requires the scope even though the generic Conventional Commits syntax
   permits omitting it.
5. For a `feat` or `fix`, include exactly one non-empty fenced `release-note`
   block unless the `release-note/skip` label applies. Write consumer-facing
   prose; PR Metadata sanitizes and validates the block before merge.
6. Write the PR body for a public reader. Include what changed, why it changed,
   non-goals, review order, validation evidence, known gaps, and rollback notes.
7. Include the validation commands that match the changed surfaces.

Good titles keep both pieces: the Conventional Commit prefix and plain English
after the colon. Avoid internal-only codes in the title or body.

Primary sources: [pull request template](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/pull_request_template.md) and [PR Metadata workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-metadata.yml).

## Maintainer Release Readiness

Use this command block as the consolidated release-readiness checklist. Run the
commands that match the PR surface and explain any skipped command in the PR
body.

```text
python3 tests/speckit-pro/check-toolchain.py --mode tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py
python3 tests/speckit-pro/run-all.py
python3 tests/speckit-pro/check-toolchain.py --mode docs
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
```

What each command proves:

| Command | Use when | Evidence it provides |
|---------|----------|----------------------|
| `python3 tests/speckit-pro/check-toolchain.py --mode tests` | Before repository validation or when tool versions are in question | Requires Python 3.11+ and `git`; reports optional `gh`, `specify`, `claude`, and `codex` tools without making them prerequisites for the deterministic suite. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py` | Plugin source, runner trust metadata, versions, or payloads changed | Idempotently rebuilds Claude and Codex payloads and synchronizes marketplace versions. PR Checks runs the same refresh and fails if it produces an uncommitted diff. |
| `python3 tests/speckit-pro/run-all.py` | Release readiness, especially plugin or release-affecting work | Runs the automatic toolchain gate and default deterministic Layers 1, 4, and 5 from `suite-manifest.json`. |
| `python3 tests/speckit-pro/check-toolchain.py --mode docs` | Before docs-site validation | Verifies Node 22+, Corepack, `pnpm@10.25.0`, installed docs dependencies, and Playwright. |
| `pnpm --dir docs-site reference:check` | Generated reference drift is possible | Verifies generated reference pages match the generator. |
| `pnpm --dir docs-site validate` | Any `docs-site/**` file changed | Runs `reference:check`, `astro check`, and `astro build` through the docs-site script chain. |

The runner's `--all` flag is not a larger deterministic release gate. It
implies live mode, executes Layers 1, 4, 5, and live Layer 6, prints manual
command plans for live-only Layers 2 and 3, and does not select gate-only
Layer 7. Use the no-flag command above for deterministic release readiness.

`pnpm --dir docs-site validate` is required for changes under `docs-site/**`.
Non-site Markdown changes do not automatically require docs-site validation, but
they still need reviewable evidence that matches the PR scope.

Maintainer validation has three toolchain buckets:

| Bucket | Required tools |
|---|---|
| Installed plugin runtime | Python 3.11+ and the official Spec Kit CLI in the target project environment. |
| Deterministic plugin suite | Python 3.11+ and `git`. The runner and repository helpers use the standard library and do not require Bash or `jq`. |
| Docs-site validation | Node 22 or newer, Corepack, `pnpm@10.25.0`, installed `docs-site` dependencies, and Playwright for smoke validation. |

Live, AI-backed, or PR-backed validation can additionally require authenticated
`gh`, `specify`, `claude`, `codex`, and the skill-creator plugin depending on the
layer.

Primary sources: [suite manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/suite-manifest.json), [unit tests](https://github.com/racecraft-lab/racecraft-plugins-public/tree/main/tests/speckit-pro/unit), [run-all.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/run-all.py), [check-toolchain.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/tests/speckit-pro/check-toolchain.py), [refresh-release-artifacts.py](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/refresh-release-artifacts.py), and [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json).

## Version Fields

Treat cache identity and version fields as owned by their source hierarchy:

- The Claude source manifest and Claude marketplace entry intentionally omit
  `version`. For a relative path in a git-hosted marketplace, Claude Code then
  uses the resolved commit SHA for update detection and the cache key. Do not
  add either field back: a static manifest version masks newer commits and can
  leave installed skill bytes stale. See Anthropic's
  [version-management reference](https://code.claude.com/docs/en/plugins-reference#version-management).
- Release-please owns release version bumps for the Codex source plugin
  manifest, the runner manifest's `plugin_version`, and the Codex marketplace
  registry version configured in `release-please-config.json`.
- `scripts/refresh-release-artifacts.py` recomputes runner trust metadata,
  rebuilds generated payloads under `dist/`, synchronizes marketplace versions
  from source manifests.
- `scripts/sync_release_pr.py` runs that refresh and the docs reference generator
  on the release PR branch, then commits and pushes the generated outputs when
  they changed.
- Manual Codex or runner version edits should be rare and explicitly explained,
  such as a maintainer-approved release recovery.

Primary sources: [release-please-config.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/release-please-config.json), [.release-please-manifest.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.release-please-manifest.json), [Claude plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.claude-plugin/plugin.json), [Codex plugin manifest](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/.codex-plugin/plugin.json), [Claude marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.claude-plugin/marketplace.json), and [Codex marketplace registry](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.agents/plugins/marketplace.json).

## Release Automation

The maintainer-facing release flow is:

1. A push to `main`, typically from a squash merge, triggers the Release
   workflow.
2. Release-please opens or updates a release PR when releasable Conventional
   Commits exist.
3. The workflow resolves both newly created and already open release PRs,
   validates release readiness, merges current `main` into each resolved
   release branch, and runs `scripts/sync_release_pr.py`. That helper refreshes
   payloads, marketplace versions, and
   generated references, then commits and pushes any changes onto the release
   PR branch. The workflow also dispatches `PR Checks` and `PR Metadata` as a
   fallback.
4. `PR Checks` validates every commit cited by a maintainer in a resolved review
   thread on a generated release PR. If regeneration drops a cited commit, the
   existing required `validate-workflows` check fails before merge.
5. When the release PR is merged, release-please publishes the GitHub Release.
   Post-release gates regenerate the docs reference and fail if `main` is not
   already artifact-consistent; the workflow does not open a second sync PR.
6. `capture-release-note-inputs` captures the release action's raw body, tag,
   Compare API response, and referenced PR bodies and labels as canonical JSON.
   It uploads that complete input set as a uniquely named, immutable artifact
   with a recorded SHA-256 and 90-day retention.
7. `compose-release-notes` downloads that exact artifact by ID and rejects any
   artifact digest, snapshot SHA-256, schema, repository, tag, or provenance
   mismatch. `scripts/compose-release-notes.py` builds consumer Highlights from
   validated `release-note` blocks and bounded fallbacks, preserves the raw
   release-please body under `## Commit appendix`, and patches the GitHub
   Release. A persisted digest marker makes reruns idempotent.
8. The workflow reads the published release back, verifies its structure,
   count metadata, byte length, and digests against the captured snapshot and
   composer result, then uploads a separate immutable release-note audit
artifact with 90-day retention. Composition or verification failures leave
an audit record and fail the workflow loudly.

The repository releases two components, `speckit-pro` and `typesafe-jev`, each
with its own release PR (`separate-pull-requests`) and its own tags
(`speckit-pro-vX.Y.Z`, `typesafe-jev-vX.Y.Z`). Release notes for one component
leave out pull requests whose Conventional Commits scope names the other.
`typesafe-jev` releases as a draft with its tag already pushed.
`typesafe-jev-assets` builds `evaluate-<os>-<arch>.tar.gz` and `SHA256SUMS.txt`
from the tag with `scripts/build-typesafe-jev-release.py`, attaches them, and
checks the draft's own assets. `typesafe-jev-publish` runs in the `release`
environment. It publishes the draft without marking it latest, then installs it
with the plugin's installer. Its release notes are then captured and composed
like `speckit-pro`'s. The component's history starts at the import merge, which
`last-release-sha` in `release-please-config.json` names.

Release-please branches are generated state. Never push a product, security,
documentation, or review fix directly to a branch whose name starts with
`release-please--branches--`. Land the fix on `main` through its own pull
request, then let release-please regenerate and the Release workflow reconcile
the release PR. A direct release-branch commit can be discarded by the next
regeneration; the ancestry check is the fail-closed backstop for any resolved
review reply that cites such a commit.

The manual `PR Checks` and `PR Metadata` dispatch is observable repository
behavior. If you
explain the GitHub-token reason, scope it to this repository's workflow comments
and GitHub's recursion guard behavior rather than treating it as a general
platform rule for every event.

Primary sources: [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), [release PR synchronizer](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/sync_release_pr.py), [artifact refresh](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/refresh-release-artifacts.py), and [release-note composer](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/scripts/compose-release-notes.py).

## Current PR Checks Behavior

`PR Checks` runs on non-draft pull requests when they open, reopen, receive a
push, or leave draft. The Release workflow can also dispatch it for
release-please PR branches. A newer push cancels the superseded run for the same
pull request; dispatched runs are never cancelled.

`PR Metadata` holds the title and release-note checks. It also reruns when the
title, body, or labels change, so those edits take seconds and never rerun the
test suite. The Release workflow dispatches it alongside `PR Checks`.

Current behavior to account for in review:

- `detect` currently emits the fixed Python-gated `speckit-pro` matrix, so every
  non-draft PR runs the toolchain and default-suite runner gates.
- `artifact-consistency` runs `scripts/refresh-release-artifacts.py`, stages the
  result, and fails when generated payloads or marketplace registries drift
  from source.
- `validate-plugins` is the stable branch-protection sentinel for the plugin
  matrix and artifact-consistency result.
- `validate-pr-title` (in `PR Metadata`) checks the Conventional Commit title
  contract. `validate-release-note` (in `PR Metadata`) separately enforces the
  `feat`/`fix` release-note block contract.
- `validate-workflows` checks GitHub Actions syntax and semantics.
- `validate-docs` always reports but chooses a no-op, generated-reference, or
  full docs-site validation mode from the changed paths. Full mode runs the
  Astro/Starlight build and Playwright smoke checks; generated-reference mode
  checks reference drift and docs quality.

Primary sources: [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml) and [PR Metadata workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-metadata.yml).

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
- `scripts/refresh-release-artifacts.py` ran and its outputs were committed when
  source changes can affect generated release artifacts, or the PR explains why
  it was not applicable.
- `python3 tests/speckit-pro/run-all.py` ran for release readiness or the PR body
  explains why it was not needed.
- `pnpm --dir docs-site validate` ran for any `docs-site/**` change.
- The PR title uses Conventional Commit format and plain English.
- A `feat` or `fix` PR contains exactly one valid fenced `release-note` block or
  carries the `release-note/skip` label.
- The PR body is public-readable and includes validation evidence, known gaps,
  and rollback notes.

Primary sources: [AGENTS.md](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/AGENTS.md), [PR Checks workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/pr-checks.yml), [Release workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/.github/workflows/release.yml), and [docs-site/package.json](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/docs-site/package.json).
