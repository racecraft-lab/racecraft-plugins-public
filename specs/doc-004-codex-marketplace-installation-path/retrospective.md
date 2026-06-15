---
feature: DOC-004 Codex marketplace installation path
branch: doc-004-codex-marketplace-installation-path
date: 2026-06-15
completion_rate: 100
spec_adherence: 100
requirements:
  implemented: 26
  partial: 0
  not_implemented: 0
  modified: 0
  unspecified: 0
findings:
  critical: 0
  significant: 0
  minor: 2
  positive: 3
---

# Retrospective: DOC-004 Codex marketplace installation path

## Executive Summary

DOC-004 completed as a documentation/process-only feature with 20/20 tasks complete and 26/26 requirement or success-criteria IDs implemented. The implementation stayed within the planned user-facing scope: Codex install guidance, README alignment, generated README documentation sync, and SDD evidence. No constitution violations or spec changes are proposed.

## Proposed Spec Changes

None.

No `spec.md` edits are recommended. The observed issues were process/evidence management details, not product requirement gaps.

## Requirement Coverage Matrix

| Requirement set | Count | Status | Evidence |
|-----------------|------:|--------|----------|
| FR-001 through FR-019 | 19 | Implemented | `docs-site/src/content/docs/install/codex.md`, `README.md`, `speckit-pro/README.md`, `tasks.md`, `verify-tasks-report.md` |
| SC-001 through SC-007 | 7 | Implemented | `tasks.md`, Phase 7 evidence, `verify-tasks-report.md`, final reviewability gate |

Spec adherence formula: `(26 implemented + 0 modified + 0 partial * 0.5) / (26 total - 0 unspecified) = 100%`.

## Success Criteria Assessment

| Success criterion | Result | Evidence |
|-------------------|--------|----------|
| SC-001 | Pass | Three entry points agree on Codex marketplace, generated payload, installed cache, custom-agent registration, restart, verification, stale-update, and safety guidance. |
| SC-002 | Pass | Install matrix and compact path list support repo-scoped, personal/local, and CLI paths. |
| SC-003 | Pass | Docs list the nine installer-copied TOML custom-agent files and exclude source-only TOML files as expected installed output. |
| SC-004 | Pass | Install safety guidance appears before users approve marketplace, network, cache, or custom-agent writes. |
| SC-005 | Pass | `pnpm validate`, `pnpm validate:links`, full shell suite, and command-snippet review all passed. |
| SC-006 | Pass | Accessibility review passed for headings, links, command labels, text-visible warnings, and matrix fallback. |
| SC-007 | Pass | Stale-after-update checkpoint points to marketplace source, generated payload, installed cache, custom-agent destination, restart state, DOC-007, and DOC-008. |

## Architecture Drift

| Planned constraint | Actual result | Drift |
|--------------------|---------------|-------|
| Documentation/spec artifacts only | User-facing docs, SDD evidence, and generated README documentation were updated. No manifests, generated payload behavior, TOML templates, install scripts, hooks, release automation, or runtime code changed. | None |
| One focused Codex install page plus README consistency | Implemented exactly across the docs-site Codex page, root README, and plugin README. | None |
| DOC-007 and DOC-008 own deeper reference/security work | DOC-004 links/defer deeper topics and does not expand into full troubleshooting or trust lifecycle. | None |

## Significant Deviations

None.

## Minor Findings

| Severity | Finding | Evidence | Recommendation |
|----------|---------|----------|----------------|
| MINOR | Final reviewability backstop warns at the total-file and primary-surface thresholds because SDD/process artifacts are intentionally included. | `gate-state.json` shows `status=warn`, `total_files=25`, `primary_surface_count=4`, and `blocked_operations=[]`. | For future docs/process specs, expect process evidence to consume file-count budget and refresh the final gate after evidence-only commits. |
| MINOR | Source README install guidance changes require generated dist README files to be committed so CI's payload-current check passes. | CI initially failed `validate-plugin-payload`; local Layer 1 passed after syncing `dist/claude/speckit-pro/README.md` and `dist/codex/speckit-pro/README.md`. | Treat generated README sync as documentation-only payload maintenance, and record it explicitly when README content changes. |

## Innovations and Best Practices

| Type | Improvement | Reuse potential |
|------|-------------|-----------------|
| POSITIVE | Source-backed command/path snippet checklist grouped Codex commands, marketplace forms, payload/cache paths, `$install`, TOML files, hooks, and safety wording. | Reuse for DOC-005/DOC-007/DOC-008 install/reference pages. |
| POSITIVE | Dense install matrix includes a compact list fallback for mobile and screen-reader review. | Reuse for future docs-site install decision pages. |
| POSITIVE | Verify-tasks phantom check created an independent 20/20 task evidence report. | Reuse as a post-implementation check for docs-heavy specs. |

## Constitution Compliance

| Principle | Result | Evidence |
|-----------|--------|----------|
| Plugin Structure Compliance | Pass | No plugin manifests, generated payload behavior, hooks, skills, agents, or marketplace behavior changed; generated README docs were synced for CI. |
| Script Safety | Pass | No scripts were changed. |
| Test Coverage Before Merge | Pass | Docs validation and `bash tests/speckit-pro/run-all.sh` passed. |
| KISS, Simplicity, and YAGNI | Pass | Scope stayed on one Codex page plus README alignment. |
| Conventional Commits | Pass | Branch commits and PR title use conventional commit style. |

Constitution violations: None.

## Unspecified Implementations

None that affect product behavior. Additional process artifacts were produced for verification and PR readiness:

- `verify-tasks-report.md`
- `.process/final-reviewability/gate-state.json`
- Autopilot workflow/state updates
- Generated payload README sync in `dist/claude/speckit-pro/README.md` and `dist/codex/speckit-pro/README.md`

## Task Execution Analysis

- Total tasks: 20
- Completed tasks: 20
- Completion rate: 100%
- Dropped tasks: 0
- Added implementation tasks outside `tasks.md`: 0

All completed tasks map back to FR-001 through FR-019 and SC-001 through SC-007 in `tasks.md`.

## Lessons Learned and Recommendations

1. Keep PR packet/body artifacts transient when they would push a docs/process diff over reviewability file-count thresholds.
2. Re-run final reviewability after evidence-only commits that add tracked files, even when no user-facing docs changed.
3. Keep source-backed snippet review tables in the workflow for Codex docs because official docs, CLI help, generated payloads, and installer behavior all contribute to correct install wording.
4. Preserve generated-dist sync notes whenever full validation or CI rewrites generated payload README files during docs-only work.

## Self-Assessment Checklist

| Check | Result |
|-------|--------|
| Evidence completeness | PASS |
| Coverage integrity | PASS |
| Metrics sanity | PASS |
| Severity consistency | PASS |
| Constitution review | PASS |
| Human Gate readiness | PASS |
| Actionability | PASS |

## File Traceability Appendix

| File | Role |
|------|------|
| `docs-site/src/content/docs/install/codex.md` | Primary DOC-004 install guidance. |
| `README.md` | Root install entry point aligned to docs-site guidance. |
| `speckit-pro/README.md` | Plugin README install entry point aligned to docs-site guidance. |
| `specs/doc-004-codex-marketplace-installation-path/spec.md` | Requirements and success criteria source. |
| `specs/doc-004-codex-marketplace-installation-path/plan.md` | Implementation approach and constraints. |
| `specs/doc-004-codex-marketplace-installation-path/tasks.md` | Task traceability and completion state. |
| `specs/doc-004-codex-marketplace-installation-path/verify-tasks-report.md` | Independent task verification evidence. |
| `specs/doc-004-codex-marketplace-installation-path/.process/final-reviewability/gate-state.json` | Final reviewability gate evidence. |
| `dist/claude/speckit-pro/README.md` | Generated Claude payload README synced from source README. |
| `dist/codex/speckit-pro/README.md` | Generated Codex payload README synced from source README. |

Retrospective saved. Adherence: 100%. Critical findings: 0.
