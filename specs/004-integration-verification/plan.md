# Implementation Plan: Integration & Verification

**Branch**: `004-integration-verification` | **Date**: 2026-04-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-integration-verification/spec.md`

## Summary

Configure GitHub branch protection on `main` via the legacy REST API (requiring `validate-plugins` and `validate-pr-title` status checks, squash-only merges, and admin-bypass for GITHUB_TOKEN), add a `validate-plugins` sentinel aggregator job to pr-checks.yml, configure Copilot code review via UI (documented steps only), and produce three documentation artifacts: an end-to-end verification checklist, five new CLAUDE.md sections, and copy-pasteable recovery procedures. One structural test file is added to validate the sentinel job configuration (a justified deviation from FR-012, which was scoped to prevent plugin logic changes — not to prevent CI validation of CI changes).

## Technical Context

**Language/Version**: Bash (gh CLI v2+), Markdown (GitHub-Flavored)
**Primary Dependencies**: GitHub CLI (`gh`), GitHub Actions (existing YAML workflows)
**Storage**: N/A
**Testing**: Manual end-to-end walkthrough (verification checklist) — no automated test additions
**Target Platform**: GitHub (racecraft-lab/racecraft-plugins-public, personal repo)
**Project Type**: CI/CD configuration + documentation
**Performance Goals**: N/A (configuration)
**Constraints**: Legacy branch protection API only (no rulesets); Copilot review UI-only; `enforce_admins: false` bypass (personal repo); no new test files; no existing plugin code changes; sentinel job must pass on skipped matrix
**Scale/Scope**: Single repository, single protected branch (`main`), two required status checks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Principle | Status | Notes |
|------|-----------|--------|-------|
| Structural validation | I. Plugin Structure | PASS | No plugin directories modified |
| Script safety | II. Script Safety | PASS | No new bash scripts |
| Version format | III. Semantic Versioning | PASS | No version changes |
| Test coverage | IV. Test Coverage | PASS | No new code under test; existing `bash tests/run-all.sh` unchanged |
| Commit format | V. Conventional Commits | PASS | Branch protection enforces this going forward; `validate-plugins` sentinel adds the aggregator |
| KISS + scope justification | VI. KISS/Simplicity | PASS | Legacy API used (simpler than rulesets); manual checklist (no automation overhead); all content is minimal and purposeful |

**Post-Design Re-check (Phase 1)**: PASS — The sentinel job design is the simplest approach (one `if: always()` aggregator job with a small shell expression). The five CLAUDE.md sections are additive only. The verification checklist is a flat markdown file with no scripting.

## Project Structure

### Documentation (this feature)

```text
specs/004-integration-verification/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code / Config changes (repository root)

```text
.github/workflows/
└── pr-checks.yml         # ADD: validate-plugins sentinel job (FR-013)

CLAUDE.md                 # ADD: 5 new sections (FR-009, FR-010)

docs/ai/specs/
└── cicd-release-pipeline-verification.md   # CREATE: verification checklist (FR-007, FR-008)
```

**Structure Decision**: Flat — this spec has no new source directories. Changes are targeted to three existing files and one new documentation file. YAGNI; no new directories needed.

## Complexity Tracking

> No constitution violations required. All decisions use the simplest available approach.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none) | — | — |
