# Workflow Contract: release.yml

**Date**: 2026-04-01 | **Branch**: `003-release-automation`

## Trigger

```yaml
on:
  push:
    branches: [main]
```

## Permissions

```yaml
permissions:
  contents: write
  pull-requests: write
```

## Job: release

**Runner**: `ubuntu-latest`

### Step 1: Release Please

```yaml
- id: release
  uses: googleapis/release-please-action@v4
```

No additional inputs required -- release-please reads `release-please-config.json` and `.release-please-manifest.json` from the repository root automatically.

### Step 2: Marketplace Sync (conditional)

**Condition**: `steps.release.outputs['speckit-pro--release_created'] == 'true'`

Sub-steps:
1. Checkout main (to get release-please's version bumps)
2. Run `bash scripts/sync-marketplace-versions.sh`
3. Configure git identity (`github-actions[bot]`)
4. Check `git diff --quiet` -- skip commit if no changes
5. Commit with message: `chore: sync marketplace.json versions [skip ci]`
6. Push to main

## Commit Contract

The sync commit MUST:
- Use conventional commit format: `chore: sync marketplace.json versions [skip ci]`
- Be authored by `github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>`
- Use GITHUB_TOKEN (not PAT) for push authentication
- Include `[skip ci]` to prevent unnecessary workflow re-runs

## Dependencies

| Dependency | Source | Status |
|------------|--------|--------|
| `release-please-config.json` | SPEC-001 | Exists |
| `.release-please-manifest.json` | SPEC-001 | Exists |
| `scripts/sync-marketplace-versions.sh` | SPEC-001 | Exists |
| Branch protection bypass for Actions bot | SPEC-004 | Pending |
