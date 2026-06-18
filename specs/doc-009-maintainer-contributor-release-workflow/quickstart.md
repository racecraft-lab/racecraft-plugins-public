# Quickstart: Maintainer and Contributor Release Workflow

## Goal

Use this quickstart to implement and verify DOC-009 without changing release behavior, CI behavior, generated payloads, marketplace registries, or version fields.

## Implementation Steps

1. Open `docs-site/src/content/docs/contribute-and-release.md` and replace the DOC-002 route shell with the DOC-009 full workflow.
2. Build the page in this order: purpose, source-of-truth map, change-type matrix, contributor path, maintainer readiness, version and release automation guidance, final checklist, DOC-010 handoff.
3. Source behavior claims from primary files:
   - `.github/workflows/pr-checks.yml`
   - `.github/workflows/release.yml`
   - `release-please-config.json`
   - `.release-please-manifest.json`
   - `scripts/build-plugin-payloads.sh`
   - `scripts/sync-marketplace-versions.sh`
   - `tests/speckit-pro/run-all.sh`
   - `docs-site/package.json`
   - `CLAUDE.md`
   - `AGENTS.md`
4. Link generated reference pages for deeper inventories:
   - `/reference/source-vs-dist/`
   - `/reference/scripts/`
   - `/reference/tests/`
   - `/reference/manifests/`
5. Keep the DOC-010 handoff explicit for future docs-site CI, search, accessibility, deep-link, responsive, and safe command-snippet validation.

## Validation Commands

Run from the repository root:

```bash
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate
bash tests/speckit-pro/run-all.sh
```

## Review Checks

- AC-9.1: The change-type matrix covers docs-only, plugin source, generated payload/dist, marketplace, and release automation changes.
- AC-9.2: The maintainer path explains payload build, marketplace sync, and full shell suite commands.
- AC-9.3: Version guidance distinguishes release-please-owned, generated, synchronized, and manually reviewed fields.
- AC-9.4: The final checklist covers source/dist parity, Claude/Codex marketplace parity, manifest consistency, and generated payload validation.
- AC-9.5: Contributor guidance covers Conventional Commit titles and public-readable PR bodies.
- AC-9.6: Docs-only PR Checks behavior is explained from the workflow, and future docs-site CI hardening is handed to DOC-010.

## Rollback

Revert the DOC-009 route and SpecKit artifact commits. No migration, data cleanup, feature flag, or release rollback is required.
