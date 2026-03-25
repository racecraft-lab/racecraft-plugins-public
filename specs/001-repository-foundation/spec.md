# Feature Specification: Repository Foundation for CI/CD Pipeline

**Feature Branch**: `001-repository-foundation`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Repository Foundation for CI/CD Pipeline - automated versioning infrastructure"

## Clarifications

### Session 2026-03-24

- Q: How should the sync script discover which plugins to process — scan for plugin.json files or use a defined list? → A: Registry-driven discovery — iterate over marketplace.json `plugins` array entries; derive each plugin.json path from the entry's `source` field
- Q: What happens when marketplace.json has a plugin entry but no corresponding plugin.json exists? → A: Exit with non-zero exit code and descriptive error message (fail fast, do not skip with warning)
- Q: What happens when a new plugin exists on disk but is not yet listed in marketplace.json? → A: The sync script ignores it silently — plugin registration in marketplace.json is a separate manual step, not the sync script's responsibility
- Q: How does the sync script match a marketplace.json entry to its plugin.json on disk? → A: Derive path from the marketplace entry's `source` field — for relative-path sources (starting with `./`), resolve `<source>/.claude-plugin/plugin.json` relative to the repo root; skip non-relative sources (external git repos)
- Q: Where should the sync script be located in the repository? → A: `scripts/sync-marketplace-versions.sh` at repository root (repo-level concern, not plugin-specific); tests remain at `speckit-pro/tests/layer4-scripts/test-sync-marketplace-versions.sh` since the test infrastructure lives under speckit-pro
- Q: Should `bump-minor-pre-major` be set as a global default in the release-please config root, per-package only, or both? → A: Per-package only — each plugin's package entry explicitly sets `bump-minor-pre-major: true`; no global default. This keeps each plugin's versioning strategy self-contained and explicit
- Q: What should `.release-please-manifest.json` contain on initial bootstrap — the current plugin versions or an empty object? → A: Pre-populated with current versions (e.g., `"speckit-pro/": "1.0.0"`) matching each plugin's `plugin.json`; an empty manifest would cause release-please to scan all commit history. A `bootstrap-sha` MAY be added to the config to limit initial changelog scanning but is not required if the manifest is pre-populated
- Q: The `simple` release type creates and maintains a `version.txt` in each package directory — should the spec account for this artifact? → A: Acknowledge but do not treat as source of truth — `version.txt` is a release-please output artifact of the `simple` strategy; `plugin.json` (updated via `extra-files` GenericJson updater) remains the authoritative version source per constitution principle III
- Q: Is the `extra-files` path format `.claude-plugin/plugin.json` correct as a package-relative path? → A: Confirmed correct — `extra-files` paths are relative to the package directory (e.g., for package `speckit-pro/`, the path `.claude-plugin/plugin.json` resolves to `speckit-pro/.claude-plugin/plugin.json`). Repo-root-absolute paths (prefixed with `/`) are only needed for files outside the package directory

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Release-Please Configuration (Priority: P1)

As a maintainer, I need release-please configuration files so that conventional commits on main automatically trigger version bumps and changelog generation for each plugin independently.

**Why this priority**: Without the release-please configuration, no automated versioning can happen. This is the foundational artifact that all subsequent CI/CD pipeline specs depend on. It enables the shift from manual to automated version management.

**Independent Test**: Can be fully tested by validating that the configuration files are valid JSON, reference the correct plugin paths, and use the correct release-type and updater settings. Delivers the configuration foundation for automated releases.

**Acceptance Scenarios**:

1. **Given** the repository has no release-please configuration, **When** `release-please-config.json` is created, **Then** it contains a packages entry for `speckit-pro/` with `release-type: "simple"` and `bump-minor-pre-major: true`
2. **Given** a release-please configuration exists for `speckit-pro/`, **When** the `extra-files` section is inspected, **Then** it includes a GenericJson updater entry targeting `.claude-plugin/plugin.json` at `$.version`
3. **Given** release-please configuration exists, **When** `.release-please-manifest.json` is created, **Then** it contains an entry for `speckit-pro/` with the current version matching `speckit-pro/.claude-plugin/plugin.json`
4. **Given** a new plugin directory is added to the repository in the future, **When** the maintainer updates the release-please configuration, **Then** the new plugin can be added as an independent package entry without affecting existing plugin versioning

---

### User Story 2 - Marketplace Version Sync Script (Priority: P1)

As a maintainer, I need a sync script that reads each plugin's `plugin.json` version and updates the matching entry in `marketplace.json`, so version information stays consistent without manual intervention.

**Why this priority**: This directly solves the version duplication problem. Even with release-please bumping `plugin.json`, the marketplace registry will remain stale without a sync mechanism. This story and Story 1 together form the minimum viable foundation.

**Independent Test**: Can be fully tested by running the script against a repo with known version mismatches and verifying that `marketplace.json` is updated to match each plugin's `plugin.json` version.

**Acceptance Scenarios**:

1. **Given** `speckit-pro/.claude-plugin/plugin.json` has version `0.6.0` and `.claude-plugin/marketplace.json` has version `0.5.0` for the `speckit-pro` entry, **When** the sync script runs, **Then** `.claude-plugin/marketplace.json` is updated to show version `0.6.0` for `speckit-pro`
2. **Given** `plugin.json` and `marketplace.json` already have matching versions, **When** the sync script runs, **Then** `marketplace.json` remains unchanged (no unnecessary file modifications)
3. **Given** the marketplace has entries for multiple plugins, **When** the sync script runs, **Then** each plugin's marketplace entry is updated independently based on its own `plugin.json`
4. **Given** a plugin directory listed in `marketplace.json` does not contain a valid `plugin.json`, **When** the sync script runs, **Then** the script exits with a non-zero exit code and a descriptive error message

---

### User Story 3 - Version Source of Truth Alignment (Priority: P2)

As a maintainer, I need the version duplication problem fixed so that `plugin.json` is the unambiguous source of truth, aligned with Anthropic's documented behavior.

**Why this priority**: This is a documentation and governance concern. The technical fix is delivered by Stories 1 and 2 together, but this story ensures the rationale is captured and the version flow is clearly defined for future contributors.

**Independent Test**: Can be verified by confirming that after release-please bumps `plugin.json` and the sync script runs, `marketplace.json` reflects the same version, and no manual version edits are required.

**Acceptance Scenarios**:

1. **Given** a release-please release PR is merged, **When** the version bump is applied, **Then** `plugin.json` is updated as the primary version file and `marketplace.json` is subsequently synced to match
2. **Given** a contributor manually edits the version in `marketplace.json`, **When** the sync script runs, **Then** the manual edit is overwritten with the version from `plugin.json`

---

### User Story 4 - Sync Script Unit Tests (Priority: P2)

As a maintainer, I need Layer 4 unit tests for the sync script so that regressions are caught before merge.

**Why this priority**: Tests protect the sync script from regressions as the repository evolves. Without tests, future changes to marketplace structure or plugin layout could silently break version synchronization.

**Independent Test**: Can be tested by running the test suite and verifying all assertions pass, covering both happy-path and error scenarios.

**Acceptance Scenarios**:

1. **Given** the test suite exists at `tests/layer4-scripts/test-sync-marketplace-versions.sh`, **When** the tests run, **Then** they validate that the sync script correctly updates mismatched versions
2. **Given** the test suite is run, **When** a test fixture has a plugin with no `plugin.json`, **Then** the test validates the sync script exits with a non-zero code
3. **Given** the test suite uses the shared assertions library, **When** the tests are executed via `bash tests/run-all.sh --layer 4`, **Then** they integrate seamlessly with the existing test runner

---

### Edge Cases

- **Orphaned marketplace entry**: When `marketplace.json` references a plugin whose `source` path does not contain a valid `plugin.json`, the sync script MUST exit with a non-zero exit code and a descriptive error message identifying the missing file (per FR-008). This is a data integrity error that must block CI.
- **Missing version field**: When `plugin.json` exists but has no `version` field, the sync script MUST exit with a non-zero exit code and report which plugin is missing the field.
- **Malformed marketplace.json**: When `marketplace.json` has invalid JSON, `jq` will fail and `set -e` will cause the script to exit with a non-zero code. The error message from `jq` is sufficient.
- **Wrong working directory**: When the sync script is run from a directory other than the repository root, it MUST detect this (e.g., by checking for `.claude-plugin/marketplace.json` existence) and exit with an error directing the user to run from the repo root.
- **Missing jq**: When `jq` is not installed, the script MUST check for it at startup and exit with a clear error message instructing the user to install jq.
- **Non-relative source in marketplace.json**: When a marketplace entry uses a non-relative source (e.g., a GitHub repo object), the sync script MUST skip that entry silently — external plugins manage their own versions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Repository MUST contain a `release-please-config.json` at the root with a packages entry for each plugin directory, using `release-type: "simple"`
- **FR-002**: Each package entry in `release-please-config.json` MUST include `bump-minor-pre-major: true` at the per-package level (not as a global default), keeping each plugin's versioning strategy explicit and self-contained
- **FR-003**: Each package entry in `release-please-config.json` MUST include an `extra-files` array with a GenericJson updater entry in the format `{"type": "json", "path": ".claude-plugin/plugin.json", "jsonpath": "$.version"}`
- **FR-004**: Repository MUST contain a `.release-please-manifest.json` at the root, pre-populated with version entries matching each plugin's current `plugin.json` version (e.g., `{"speckit-pro/": "1.0.0"}`). This pre-population is required for initial bootstrap — an empty manifest would cause release-please to scan the entire commit history
- **FR-005**: Repository MUST contain a sync script at `scripts/sync-marketplace-versions.sh` that iterates over the `plugins` array in `.claude-plugin/marketplace.json`, derives each plugin's `plugin.json` path from the entry's `source` field (resolving relative paths like `./speckit-pro` to `<source>/.claude-plugin/plugin.json`), reads the version, and writes it back to the corresponding marketplace entry's `version` field. Non-relative sources (external git repos) MUST be skipped silently. Plugins on disk but not listed in marketplace.json MUST be ignored (registration is a separate manual step)
- **FR-006**: The sync script MUST use `jq` for all JSON manipulation (no sed/awk string hacking)
- **FR-007**: The sync script MUST follow existing shell script conventions: `#!/usr/bin/env bash` shebang and `set -euo pipefail`
- **FR-008**: The sync script MUST exit with a non-zero exit code and descriptive error message when a plugin's `plugin.json` is missing or unreadable
- **FR-009**: The sync script MUST be idempotent -- running it when versions already match MUST NOT modify `marketplace.json`
- **FR-010**: Repository MUST contain Layer 4 unit tests for the sync script at `tests/layer4-scripts/test-sync-marketplace-versions.sh`
- **FR-011**: Unit tests MUST use the shared assertions library at `tests/lib/assertions.sh`
- **FR-012**: Unit tests MUST cover at minimum: version mismatch correction, already-matching versions (no-op), missing `plugin.json` error handling, and multi-plugin sync scenarios

### Key Entities

- **plugin.json**: Per-plugin manifest containing the authoritative version number. Located at `<plugin-dir>/.claude-plugin/plugin.json`
- **marketplace.json**: Repository-level registry of all available plugins and their versions. Located at `.claude-plugin/marketplace.json`
- **release-please-config.json**: Configuration file that tells release-please how to manage versions for each package in the monorepo
- **.release-please-manifest.json**: Manifest tracking the current released version of each package, used by release-please to determine the next version bump
- **sync script**: Shell script at `scripts/sync-marketplace-versions.sh` (repository root level) that iterates over marketplace.json entries and synchronizes version numbers from each local plugin's `plugin.json` into the marketplace registry
- **version.txt**: Auto-generated output artifact of the `simple` release type strategy. Created and maintained by release-please in each package directory. NOT the source of truth for version information — `plugin.json` remains authoritative per constitution principle III (Semantic Versioning)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All release-please configuration files pass JSON validation and contain correct entries for every plugin in the repository
- **SC-002**: Running the sync script on a repository with intentionally mismatched versions corrects 100% of version entries in `marketplace.json`
- **SC-003**: Running the sync script when versions already match produces zero file modifications
- **SC-004**: All Layer 4 unit tests pass when executed via the existing test runner (`bash tests/run-all.sh --layer 4`)
- **SC-005**: The sync script completes execution in under 5 seconds for a repository with up to 10 plugins
- **SC-006**: The sync script produces a clear, actionable error message for every failure mode (missing file, missing field, invalid JSON)

## Assumptions

- The repository uses conventional commits on the main branch, which is a prerequisite for release-please to function
- The `jq` command-line tool is available in the development and CI environments
- The existing test runner at `tests/run-all.sh` supports discovering and executing new Layer 4 test files without modification
- The `.claude-plugin/marketplace.json` structure uses a `plugins` array where each entry has a `name` field, a `source` field (relative path like `"./speckit-pro"` for local plugins), and a `version` field. The sync script uses the `source` field (not the `name` field) to locate each plugin's `plugin.json` on disk
- The `extra-files` paths in release-please configuration are relative to the package directory, not the repository root (confirmed via release-please documentation and issue #2477 — repo-root-absolute paths use a `/` prefix, which is not needed here since `plugin.json` is inside the package directory)
- The `simple` release type creates a `version.txt` file in each package directory as an output artifact; this file is not the version source of truth and should not be manually edited
- GitHub Actions workflow files that invoke release-please and the sync script are out of scope for this spec (covered by SPEC-002 and SPEC-003)
- Branch protection rules are out of scope (covered by SPEC-004)
