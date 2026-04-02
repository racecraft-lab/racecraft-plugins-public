# Quickstart: Repository Foundation for CI/CD Pipeline

**Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)

## What This Feature Does

Sets up automated version management for the racecraft-plugins-public repository:

1. **release-please configuration** -- Tells Google's release-please tool how to bump versions in each plugin's `plugin.json` when conventional commits land on `main`.
2. **Marketplace version sync script** -- Reads each plugin's `plugin.json` version and updates the matching entry in `.claude-plugin/marketplace.json` so the registry stays consistent.
3. **Unit tests** -- Layer 4 tests for the sync script following the existing test patterns.

## Files Created

| File | Purpose |
|------|---------|
| `release-please-config.json` | Per-plugin release configuration (simple strategy, GenericJson updater) |
| `.release-please-manifest.json` | Current version tracker for release-please (pre-populated with 1.0.0) |
| `scripts/sync-marketplace-versions.sh` | Syncs plugin.json versions into marketplace.json |
| `speckit-pro/tests/layer4-scripts/test-sync-marketplace-versions.sh` | Unit tests for the sync script |

## How to Verify

```bash
# 1. Validate release-please config is valid JSON
python3 -c "import json; json.load(open('release-please-config.json'))"
python3 -c "import json; json.load(open('.release-please-manifest.json'))"

# 2. Run the sync script (should be a no-op if versions already match)
bash scripts/sync-marketplace-versions.sh

# 3. Run the unit tests
bash speckit-pro/tests/run-all.sh --layer 4
```

## How the Sync Script Works

```text
1. Verify prerequisites (jq installed, marketplace.json exists at repo root)
2. Read .claude-plugin/marketplace.json
3. For each plugin entry in the "plugins" array:
   a. Extract the "source" field (e.g., "./speckit-pro")
   b. Skip non-relative sources (external repos)
   c. Resolve to <source>/.claude-plugin/plugin.json
   d. Read the "version" field from plugin.json
   e. Update the marketplace entry's "version" to match
4. Write updated marketplace.json only if changes were made (idempotent)
```

## Adding a New Plugin

When a new plugin is added to the repository:

1. Create the plugin directory with `.claude-plugin/plugin.json`
2. Add a package entry to `release-please-config.json`
3. Add a version entry to `.release-please-manifest.json`
4. Add a plugin entry to `.claude-plugin/marketplace.json`
5. The sync script will automatically keep versions in sync from that point
