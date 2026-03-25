# Implementation Plan: Repository Foundation for CI/CD Pipeline

**Branch**: `001-repository-foundation` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-repository-foundation/spec.md`

## Summary

Establish the repository foundation for automated CI/CD versioning by creating release-please configuration files, a marketplace version sync script, and Layer 4 unit tests. The technical approach uses Bash + jq for the sync script, release-please's `simple` strategy with GenericJson updater for version management, and the existing shared assertions library for testing. All artifacts are configuration files and shell scripts -- no application code.

## Technical Context

**Language/Version**: Bash (POSIX-compatible, tested on macOS/Linux)
**Primary Dependencies**: jq (JSON processing), release-please (Google, version automation)
**Storage**: N/A (file-based JSON configuration only)
**Testing**: Shell-based test suite with shared assertions library (`tests/lib/assertions.sh`)
**Target Platform**: macOS (local dev) + Linux (GitHub Actions CI)
**Project Type**: CLI tool (sync script) + configuration files
**Performance Goals**: Sync script completes in under 5 seconds for up to 10 plugins (SC-005)
**Constraints**: Scripts must use `set -euo pipefail`, `jq` for JSON, `chmod +x` (Constitution II, VI)
**Scale/Scope**: 1 plugin now (speckit-pro), 2-4 plugins within 6 months

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Plugin Structure Compliance | PASS | No new plugin directories created; existing structure preserved |
| II. Script Safety | PASS | Sync script will use `#!/usr/bin/env bash` + `set -euo pipefail` + `chmod +x` + all variables quoted + all command results checked (FR-007) |
| III. Semantic Versioning | PASS | `plugin.json` remains source of truth; release-please manages bumps; sync script reads from it (FR-005) |
| IV. Test Coverage Before Merge | PASS | Layer 4 tests planned at `tests/layer4-scripts/test-sync-marketplace-versions.sh` (FR-010, FR-011, FR-012) |
| V. Conventional Commits | PASS | All commits will follow `type(scope): description` format |
| VI. KISS, Simplicity & YAGNI | PASS | Sync script uses `jq` for JSON (no sed/awk); flat sequential logic; no abstractions for one-time operations |

No violations. Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-repository-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
racecraft-plugins-public/
├── release-please-config.json          # FR-001, FR-002, FR-003
├── .release-please-manifest.json       # FR-004
├── scripts/
│   └── sync-marketplace-versions.sh    # FR-005 through FR-009
└── speckit-pro/
    └── tests/
        └── layer4-scripts/
            └── test-sync-marketplace-versions.sh  # FR-010, FR-011, FR-012
```

**Structure Decision**: No new application directories needed. This feature adds configuration files at repository root and a standalone script under `scripts/`. Tests follow the existing Layer 4 pattern under `speckit-pro/tests/layer4-scripts/`. No Option template applies -- this is configuration + scripting, not an application.

## Sync Script Implementation Design

### Script Safety (Constitution II Compliance)

All variables MUST be double-quoted to prevent word splitting and globbing. All command substitutions MUST be quoted (e.g., `"$(jq ... "$file")"`). This includes loop variables, file paths, and jq output captures. The script MUST pass `shellcheck` with no warnings.

### Prerequisite Check Order and Dependency Detection

The sync script MUST check prerequisites in the following order before processing any plugins:

1. **jq dependency** -- Check using `command -v jq >/dev/null 2>&1` (POSIX-compliant builtin, consistent with `check-prerequisites.sh` pattern). If jq is not found, exit with `exit 1` and an error message to stderr instructing the user to install jq. This check MUST come first because all subsequent operations depend on jq.
2. **Working directory** -- Check for `.claude-plugin/marketplace.json` existence. If not found, exit with `exit 1` and an error message to stderr directing the user to run from the repo root.

The `command -v` builtin is preferred over `which` because it is POSIX-specified, handles shell builtins correctly, and is consistent with ShellCheck recommendation SC2230.

### Output Stream Convention

All error messages MUST be written to stderr using the `>&2` redirect (e.g., `echo "error: ..." >&2`). Informational messages (e.g., "no plugins to sync", "skipping non-relative source") MUST also go to stderr. Stdout is reserved exclusively for the sync summary (listing which plugins were updated). On no-op runs (all versions match), the script produces no stdout output. This separation ensures CI log parsers and pipeline steps can reliably distinguish errors from normal output.

### jq Filter Validation Strategy

Before iterating over marketplace entries, the script MUST validate that the `plugins` array exists and is a JSON array using `jq -e '.plugins | type == "array"'`. If the array is empty, the script MUST exit successfully with an informational message (no plugins to sync is not an error).

For each marketplace entry, the script MUST validate:
- The `source` field exists (exit with error identifying the entry by index if missing)
- After reading `plugin.json`, the `version` field exists and is non-null (exit with error identifying the plugin if missing)

The `jq -e` flag MUST be used for all existence/value checks so that `null` or `false` results produce a non-zero exit code caught by `set -e`.

### File Path Handling

The sync script resolves plugin paths from the `source` field by stripping a leading `./` prefix (if present) and appending `/.claude-plugin/plugin.json`. All path variables MUST be double-quoted to handle directory names containing spaces or special characters. The script does not need to handle newlines in directory names (this is not a realistic scenario for plugin directories).

### Semver Validation

After reading the `version` field from each plugin's `plugin.json`, the sync script MUST validate the value against the semver pattern `^[0-9]+\.[0-9]+\.[0-9]+$` (Constitution III). This prevents propagating invalid version strings to marketplace.json. Validation uses a bash regex match (`[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]`). On failure, the script exits with a non-zero code and an error message identifying the plugin and the invalid version string.

### Idempotency Implementation and Partial Sync Prevention

The script MUST build the complete updated marketplace.json content in a shell variable (in memory) before performing any file write. This single-write approach ensures that if any plugin processing fails (missing plugin.json, invalid semver, etc.), `set -euo pipefail` causes the script to exit before the write occurs, leaving marketplace.json unchanged. There is no partial sync state -- either all plugins are processed successfully and marketplace.json is written once, or the script exits with an error and marketplace.json remains untouched.

After building the updated content, the script MUST compare it with the existing file content. If versions already match, the script MUST skip the file write entirely (not write identical content). This ensures `git status` remains clean after a no-op run. Implementation approach: build the updated JSON in a variable, compare with existing file content, and only write if different.

### jq Output Format

The sync script MUST use `jq` with consistent formatting flags to ensure deterministic output for idempotency comparison. Specifically, `jq` default pretty-print (2-space indent, trailing newline) MUST be used. The `--sort-keys` flag MUST NOT be used, as it would reorder existing marketplace.json fields and produce unnecessary diffs. The `jq` tool preserves object key ordering by default, which is the desired behavior for minimal-diff writes.

### Atomic Write Decision

The sync script does NOT require atomic writes (temporary file + `mv` pattern). Rationale per Constitution VI (KISS/YAGNI):
- The file being written (`marketplace.json`) is tracked by git -- any corruption is recoverable via `git checkout`
- The script runs in CI and local dev, not in concurrent production environments
- The `jq` output is written in a single shell redirect, which is sufficient for this use case
- Adding `mktemp` + `mv` + `trap` cleanup adds complexity for a scenario (mid-write interruption of a small JSON file) that is vanishingly unlikely

If future requirements introduce concurrent script execution or non-git-tracked targets, this decision should be revisited.

### jq Write-Back Failure Handling

If `jq` fails during the write-back to `marketplace.json` (e.g., disk full, permission denied), `set -e` will cause the script to exit immediately with a non-zero code. The shell's built-in error message combined with `jq`'s stderr output is sufficient -- no custom error wrapping is needed for write failures.

## Complexity Tracking

No Constitution violations to justify. All solutions follow the simplest approach.
