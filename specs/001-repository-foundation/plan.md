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
| II. Script Safety | PASS | Sync script will use `#!/usr/bin/env bash` + `set -euo pipefail` + `chmod +x` (FR-007) |
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

## Complexity Tracking

No Constitution violations to justify. All solutions follow the simplest approach.
