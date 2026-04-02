# Data Model: Release Automation

**Date**: 2026-04-01 | **Branch**: `003-release-automation`

## Entities

### 1. Workflow Definition (`release.yml`)

The primary deliverable. A GitHub Actions workflow file.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Workflow display name: `"Release"` |
| `on.push.branches` | string[] | Trigger branches: `["main"]` |
| `permissions.contents` | string | Token permission: `"write"` |
| `jobs.release.runs-on` | string | Runner: `"ubuntu-latest"` |
| `jobs.release.steps` | Step[] | Sequential steps (see below) |

### 2. Workflow Steps

| Step ID | Name | Action/Command | Condition |
|---------|------|----------------|-----------|
| `release` | Release Please | `googleapis/release-please-action@v4` | Always (on push to main) |
| `checkout` | Checkout | `actions/checkout@v4` | `steps.release.outputs['speckit-pro--release_created'] == 'true'` |
| `sync` | Sync Marketplace Versions | `bash scripts/sync-marketplace-versions.sh` | Same condition as checkout |
| `commit-sync` | Commit and Push Sync | Inline bash (git add, commit, push) | Same condition + `git diff --quiet` check |

### 3. release-please Outputs (consumed by workflow)

| Output Variable | Type | Description |
|-----------------|------|-------------|
| `speckit-pro--release_created` | string (`'true'`/`'false'`) | Whether a release was created for speckit-pro |
| `speckit-pro--tag_name` | string | Git tag created (e.g., `speckit-pro-v1.1.0`) |
| `speckit-pro--version` | string | Version number (e.g., `1.1.0`) |

### 4. Existing Configuration Files (NOT modified)

| File | Purpose | Managed By |
|------|---------|-----------|
| `release-please-config.json` | Package config, release type, extra-files | SPEC-001 |
| `.release-please-manifest.json` | Version tracker (`{"speckit-pro": "1.0.0"}`) | release-please (auto-updated) |
| `scripts/sync-marketplace-versions.sh` | Registry-driven marketplace version sync | SPEC-001 |

## State Transitions

```text
Push to main
    |
    v
release-please runs
    |
    +--> No releasable commits --> exit (no-op)
    |
    +--> Releasable commits exist
         |
         +--> No Release PR exists --> Create Release PR
         |
         +--> Release PR exists --> Update Release PR
         |
         +--> Release PR was just merged --> Create Release + Tag
              |
              v
         Marketplace sync condition: release_created == 'true'
              |
              v
         Run sync script --> git diff check
              |
              +--> No changes --> exit (idempotent)
              |
              +--> Changes exist --> commit + push
                   (chore: sync marketplace.json versions [skip ci])
```

## Validation Rules

- Workflow YAML must be valid GitHub Actions syntax
- Permissions block must specify `contents: write` (not `write-all`)
- release-please step must have `id: release` for output references
- Sync condition must use `speckit-pro--release_created` (singular, path-prefixed)
- Sync commit message must be exactly `chore: sync marketplace.json versions [skip ci]`
- Git identity must be configured before commit step
