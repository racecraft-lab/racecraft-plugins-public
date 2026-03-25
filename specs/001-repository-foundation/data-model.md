# Data Model: Repository Foundation for CI/CD Pipeline

**Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)

## Entities

### 1. release-please-config.json

**Location**: Repository root (`./release-please-config.json`)
**Format**: JSON

```json
{
  "release-type": "simple",
  "packages": {
    "<plugin-name>": {
      "component": "<plugin-name>",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "extra-files": [
        {
          "type": "json",
          "path": ".claude-plugin/plugin.json",
          "jsonpath": "$.version"
        }
      ]
    }
  }
}
```

**Fields**:
- `release-type` (string, required): Must be `"simple"`. Defines the release strategy.
- `packages` (object, required): Map of package directory name to package config.
  - Key: Plugin directory name (e.g., `"speckit-pro"`). No trailing slash.
  - `component` (string, required): Name used in git tags (e.g., `speckit-pro-v1.0.0`).
  - `changelog-path` (string, required): Path to changelog relative to package dir.
  - `bump-minor-pre-major` (boolean, required): Must be `true` per FR-002. Set per-package, not globally.
  - `extra-files` (array, required): Files to update on version bump.
    - `type` (string): Must be `"json"` for GenericJson updater.
    - `path` (string): Package-relative path to JSON file.
    - `jsonpath` (string): JSONPath expression for version field.

**Validation rules**:
- Must be valid JSON (SC-001)
- Must contain at least one package entry
- Each package `extra-files` must include the `plugin.json` updater entry (FR-003)

### 2. .release-please-manifest.json

**Location**: Repository root (`./.release-please-manifest.json`)
**Format**: JSON

```json
{
  "<plugin-name>": "<semver-version>"
}
```

**Fields**:
- Key: Plugin directory name matching `packages` key in config (e.g., `"speckit-pro"`).
- Value: Current semver version string (e.g., `"1.0.0"`). Must match `plugin.json` version at bootstrap.

**Validation rules**:
- Must be valid JSON (SC-001)
- Keys must match `release-please-config.json` package keys
- Values must match semver pattern `^[0-9]+\.[0-9]+\.[0-9]+$`
- Pre-populated at bootstrap, managed by release-please thereafter

### 3. plugin.json (existing, not modified by this feature)

**Location**: `<plugin-dir>/.claude-plugin/plugin.json`
**Format**: JSON

**Relevant fields for sync script**:
- `version` (string, required): Semver version string. Source of truth per Constitution III.

**State transitions**:
- `manual` -> `release-please-managed`: After release-please config is set up, version bumps are automated. Manual edits prohibited except during initial plugin creation.

### 4. marketplace.json (existing, modified by sync script)

**Location**: `.claude-plugin/marketplace.json`
**Format**: JSON

**Relevant fields for sync script**:
- `plugins` (array): Array of plugin entry objects.
  - `name` (string): Plugin name (informational, not used for path resolution).
  - `source` (string): Path to plugin directory. Relative paths start with `./`. Non-relative sources are external repos.
  - `version` (string): Version synced from `plugin.json` by the sync script.

**State transitions**:
- `version` field: Updated by sync script to match `plugin.json` version. Manual edits are overwritten on next sync run.

### 5. sync-marketplace-versions.sh

**Location**: `scripts/sync-marketplace-versions.sh`
**Format**: Bash script

**Input**: Reads `marketplace.json` and each plugin's `plugin.json`
**Output**: Updates `marketplace.json` version fields in-place (or no-op if already matching)

**Error states**:
- Missing `marketplace.json` -> exit non-zero with "run from repo root" message
- Missing `jq` -> exit non-zero with install instruction
- Missing `plugin.json` for a listed plugin -> exit non-zero with descriptive error (FR-008)
- Missing `version` field in `plugin.json` -> exit non-zero with descriptive error
- Non-relative source in marketplace entry -> skip silently

## Relationships

```text
release-please-config.json ---[references]---> plugin.json (via extra-files updater)
                           ---[keys match]---> .release-please-manifest.json

marketplace.json ---[source field resolves to]---> plugin.json

sync script ---[reads]---> marketplace.json (plugins array)
            ---[reads]---> plugin.json (version field per entry)
            ---[writes]--> marketplace.json (version field per entry)
```
