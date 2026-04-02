# Research: Repository Foundation for CI/CD Pipeline

**Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Research Tasks

### 1. release-please `simple` strategy behavior with `extra-files`

**Decision**: Use `release-type: "simple"` with `extra-files` GenericJson updater targeting `.claude-plugin/plugin.json` at `$.version`.

**Rationale**: The `simple` strategy is the lightest-weight option in release-please. It does not assume any particular language ecosystem (no package.json, Cargo.toml, etc.). It creates a `version.txt` as its native artifact, and the `extra-files` mechanism allows updating arbitrary JSON files. This is the correct fit for a Claude Code plugin repo that has no language-specific package manifest.

**Alternatives considered**:
- `node` release type: Would require a `package.json` and add unnecessary npm ecosystem assumptions.
- `generic` release type: Does not exist; `simple` IS the generic option.
- Custom release strategy: Overengineered for the current need (YAGNI).

### 2. `extra-files` path resolution (package-relative vs repo-root)

**Decision**: Use package-relative path `.claude-plugin/plugin.json` (no leading `/`).

**Rationale**: Confirmed via release-please documentation and GitHub issue #2477. Paths in `extra-files` resolve relative to the package directory specified in the config key (e.g., `speckit-pro/`). A leading `/` prefix would make the path repo-root-absolute, which is only needed for files outside the package directory. Since `plugin.json` is inside `speckit-pro/.claude-plugin/`, the relative path is correct.

**Alternatives considered**:
- Repo-root-absolute path (`/speckit-pro/.claude-plugin/plugin.json`): Would work but is redundant and less portable if packages are reorganized.

### 3. Manifest pre-population vs empty bootstrap

**Decision**: Pre-populate `.release-please-manifest.json` with current versions (e.g., `{"speckit-pro": "1.0.0"}`).

**Rationale**: An empty manifest causes release-please to scan the entire git history to determine the current version, which is slow and error-prone on repos with non-conventional early commits. Pre-populating with the current `plugin.json` version gives release-please an accurate starting point.

**Alternatives considered**:
- Empty manifest + `bootstrap-sha`: Would work but adds complexity. Pre-population is simpler and sufficient.
- `bootstrap-sha` only: Still requires release-please to scan from that SHA. Pre-population avoids scanning entirely.

### 4. Manifest key format: `speckit-pro` vs `speckit-pro/`

**Decision**: Use `speckit-pro` (without trailing slash) as the manifest key, matching the packages key in `release-please-config.json`.

**Rationale**: The manifest keys must match the package keys in the config file. The design spec shows `"speckit-pro": "1.0.0"` in the manifest. release-please uses this key to map between config and manifest. The trailing slash format (`speckit-pro/`) is used in some release-please examples but is not required when the config key omits it.

**Alternatives considered**:
- `speckit-pro/` with trailing slash: Would require matching trailing slash in config packages key. The design spec does not use trailing slashes.

### 5. jq for idempotent JSON updates

**Decision**: Use `jq` with `--arg` for safe value injection and file comparison to detect no-op scenarios.

**Rationale**: `jq` is the standard CLI tool for JSON manipulation. Using `--arg` prevents injection issues with special characters in version strings. For idempotency (FR-009), the script will compare the updated JSON with the original before writing, avoiding unnecessary file modifications that would trigger noisy git diffs.

**Alternatives considered**:
- `sed`/`awk` string replacement: Explicitly prohibited by Constitution Principle VI and FR-006. Fragile with nested JSON.
- Python `json` module: Would work but adds a Python dependency. `jq` is lighter and already available in CI.

### 6. Sync script discovery mechanism

**Decision**: Registry-driven discovery -- iterate over `marketplace.json` `plugins` array entries; derive each `plugin.json` path from the entry's `source` field.

**Rationale**: Confirmed via clarification. The `source` field in marketplace.json (e.g., `"./speckit-pro"`) provides the path to the plugin directory. For relative paths (starting with `./`), resolve `<source>/.claude-plugin/plugin.json` relative to repo root. Non-relative sources (external git repos) are skipped silently.

**Alternatives considered**:
- Filesystem scanning (`find` for plugin.json files): Would discover plugins not registered in marketplace.json, which is incorrect behavior per clarification.
- Hardcoded plugin list: Not scalable and violates KISS (config-driven is simpler to maintain).

### 7. Test approach for sync script

**Decision**: Use temp directory fixtures with synthetic `plugin.json` and `marketplace.json` files. Tests invoke the sync script against these fixtures and validate output using the shared assertions library.

**Rationale**: This follows the exact pattern established by existing Layer 4 tests (e.g., `test-validate-gate.sh`). Temp directories with `trap` cleanup ensure isolation. The shared `assertions.sh` library provides `assert_eq`, `assert_contains`, `assert_exit_code`, and `assert_file_exists` which cover all test scenarios.

**Alternatives considered**:
- Testing against real repo files: Would couple tests to repo state and break isolation.
- Mock-based testing: Overengineered for shell scripts; fixture files are the Bash equivalent.

## Summary

All NEEDS CLARIFICATION items were pre-resolved in the spec's clarification session. No open unknowns remain. All technology choices align with the design spec and constitution principles.
