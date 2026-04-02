# Implementation Plan: Release Automation

**Branch**: `003-release-automation` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-release-automation/spec.md`

## Summary

Create a single GitHub Actions workflow (`.github/workflows/release.yml`) that automates the entire release pipeline: release-please detects conventional commits, manages Release PRs, creates GitHub Releases with component-prefixed tags, and a conditional marketplace sync step updates `marketplace.json` from `plugin.json` versions. The workflow leverages existing SPEC-001 infrastructure (config files, sync script) and requires zero manual intervention for the commit-to-marketplace-sync lifecycle.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflow syntax) + Bash (inline sync step)
**Primary Dependencies**: `googleapis/release-please-action@v4`, `actions/checkout@v4`, `jq` (pre-installed on `ubuntu-latest`)
**Storage**: N/A (git-managed config files only)
**Testing**: Manual integration testing via GitHub Actions runs; existing `bash speckit-pro/tests/run-all.sh` for regression
**Target Platform**: GitHub Actions (`ubuntu-latest` runner)
**Project Type**: CI/CD workflow (infrastructure-as-code)
**Performance Goals**: Complete full release cycle (commit to marketplace sync) within 5 minutes
**Constraints**: Single workflow file; GITHUB_TOKEN (not PAT) for infinite-loop prevention; branch protection exemption required from SPEC-004 for sync push
**Scale/Scope**: Single plugin (`speckit-pro`) with registry-driven sync supporting future multi-plugin expansion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Plugin Structure Compliance | PASS | No plugin structure changes; workflow file lives in `.github/` outside plugin directories |
| II. Script Safety | PASS | No new scripts created; existing `sync-marketplace-versions.sh` already has `set -euo pipefail` and passes validation |
| III. Semantic Versioning | PASS | release-please manages all version bumps; workflow enforces automated versioning per constitution |
| IV. Test Coverage Before Merge | PASS | No new bash scripts requiring Layer 4 tests; workflow is tested via GitHub Actions integration |
| V. Conventional Commits | PASS | Sync commit uses `chore: sync marketplace.json versions [skip ci]` -- valid conventional commit format |
| VI. KISS, Simplicity & YAGNI | PASS | Single workflow file, two sequential steps, no abstractions or wrapper layers; reuses existing sync script |

**Gate result**: PASS -- no violations, no complexity tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-release-automation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── release.yml          # The single deliverable for SPEC-003

# Existing files (NOT modified by SPEC-003):
release-please-config.json           # Package config (from SPEC-001)
.release-please-manifest.json        # Version tracker (from SPEC-001)
scripts/sync-marketplace-versions.sh # Marketplace sync (from SPEC-001)
speckit-pro/.claude-plugin/plugin.json   # Updated by release-please
.claude-plugin/marketplace.json          # Updated by sync script
```

**Structure Decision**: Single file delivery. The workflow file at `.github/workflows/release.yml` is the only new file. All supporting infrastructure (config files, sync script) already exists from SPEC-001.

## Complexity Tracking

> No constitution violations identified. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | --         | --                                  |
