# Research: Maintainer and Contributor Release Workflow

## Decision 1: Keep DOC-009 Documentation-Only

**Decision**: Implement DOC-009 by editing `docs-site/src/content/docs/contribute-and-release.md` and SpecKit artifacts only.

**Rationale**: The design concept and spec define DOC-009 as documentation work. `CLAUDE.md` also requires surgical edits and asks agents to avoid release/config changes unless the request requires them.

**Alternatives considered**:

- Change PR Checks or Release workflows now: rejected because DOC-010 owns future docs-site CI hardening and DOC-009 does not need behavior changes.
- Edit generated payloads or marketplace files: rejected because the page can document the existing generator and sync contracts.

## Decision 2: Use Primary Sources for Workflow Claims

**Decision**: Source every command, CI, release, version, generated-surface, and marketplace claim from checked-in primary files.

**Primary source map**:

| Topic | Primary source |
|-------|----------------|
| Existing route shell | `docs-site/src/content/docs/contribute-and-release.md` |
| Docs-site scripts | `docs-site/package.json` |
| Generated reference contract | `docs-site/scripts/generate-reference-pages.mjs` |
| PR Checks behavior | `.github/workflows/pr-checks.yml` |
| Release behavior | `.github/workflows/release.yml` |
| Release-please version ownership | `release-please-config.json`, `.release-please-manifest.json` |
| Payload rebuild | `scripts/build-plugin-payloads.sh` |
| Marketplace version sync | `scripts/sync-marketplace-versions.sh` |
| Deterministic shell suite | `tests/speckit-pro/run-all.sh` |
| Plugin source manifests | `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json` |
| Marketplace registries | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` |
| PR title/body and repo policy | `CLAUDE.md`, `AGENTS.md` |

**Rationale**: Generated reference pages are useful reader links, but the spec requires behavior claims to cite primary source files.

## Decision 3: Use a Change-Type Matrix Plus One Command Block

**Decision**: Use a change-type decision matrix for docs-only, plugin source, generated payload/dist, marketplace registry, and release automation changes. Use one consolidated release-readiness command block instead of repeating commands in every matrix row.

**Rationale**: This matches Clarify session 1 and keeps the page scannable while still showing required evidence per change type.

## Decision 4: State Docs-Site Validation from Package Scripts

**Decision**: Require `pnpm --dir docs-site validate` for changes under `docs-site/**`. State that `validate` runs `reference:check`, `check`, and `build` because that is what `docs-site/package.json` declares.

**Rationale**: This is exact current behavior and avoids promising DOC-010 CI hardening.

## Decision 5: Treat Full Shell Suite as Release-Readiness Expectation

**Decision**: Present `bash tests/speckit-pro/run-all.sh` as the release-readiness test expectation, especially for plugin or release-affecting changes, without saying current CI runs the full suite for every PR.

**Rationale**: The runner documents default deterministic layers, while `.github/workflows/pr-checks.yml` runs plugin matrix jobs only when plugin-affecting paths change.

## Decision 6: Explain Version and Release Ownership by Source Hierarchy

**Decision**: Explain version ownership in this hierarchy:

1. Release-please owns source plugin manifest version bumps for `speckit-pro/.claude-plugin/plugin.json` and `speckit-pro/.codex-plugin/plugin.json`.
2. Generated payload manifests under `dist/` are rebuilt from source by `scripts/build-plugin-payloads.sh`.
3. Marketplace registry versions are synchronized from platform manifests by `scripts/sync-marketplace-versions.sh`.

**Rationale**: `release-please-config.json` lists both source manifests under `extra-files`; the build script emits platform payload roots; the sync script maps Claude and Codex marketplace registries to their platform manifest paths.

## Decision 7: Explain Release Automation as Observable Maintainer Behavior

**Decision**: Describe release-please PR creation, release PR payload sync, manual PR Checks dispatch for release PR branches, GitHub Release publication, and post-release payload/marketplace sync PR behavior as observable maintainer events.

**Rationale**: `.github/workflows/release.yml` contains these steps directly. The page should not require readers to understand hidden implementation details beyond what maintainers observe and verify.

## Decision 8: Keep Generated References Generated

**Decision**: Link generated reference pages for deeper inventories and require `reference:generate` or `reference:check` for drift, rather than hand-editing `docs-site/src/content/docs/reference/*.md`.

**Rationale**: `docs-site/scripts/generate-reference-pages.mjs` declares the generated notice and output page list. Hand edits would conflict with the generator contract.
