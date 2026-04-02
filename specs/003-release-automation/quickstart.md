# Quickstart: Release Automation

**Date**: 2026-04-01 | **Branch**: `003-release-automation`

## What This Feature Does

Adds a single GitHub Actions workflow file (`.github/workflows/release.yml`) that automates the full release lifecycle:

1. **release-please** detects conventional commits on `main`, manages Release PRs, and creates GitHub Releases with tags
2. **marketplace sync** conditionally updates `marketplace.json` after a release is created

## Prerequisites

- Repository has `release-please-config.json` and `.release-please-manifest.json` (from SPEC-001)
- Repository has `scripts/sync-marketplace-versions.sh` (from SPEC-001)
- GitHub Actions is enabled on the repository
- Branch protection exemption for GitHub Actions bot (SPEC-004 dependency)

## Implementation Steps

1. Create `.github/workflows/release.yml` with:
   - Trigger: `push` to `main`
   - Permissions: `contents: write`, `pull-requests: write`
   - Step 1: `googleapis/release-please-action@v4` (id: `release`)
   - Step 2: Conditional checkout + sync + commit (when `speckit-pro--release_created == 'true'`)

2. The workflow file is the sole deliverable -- no other files are created or modified.

## Verification

After merging the workflow to `main`:

1. Push a `feat:` commit -- verify a Release PR is opened
2. Merge the Release PR -- verify a GitHub Release and tag are created
3. Verify `marketplace.json` is updated by the sync commit
4. Verify no infinite loop (sync commit does not trigger new releases)

## File Inventory

| File | Action | Notes |
|------|--------|-------|
| `.github/workflows/release.yml` | CREATE | Single deliverable |
