# Archival Report: PRSG-008 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-008-layer-planner` | archived in memory | cleanup applied | PR #138 is merged, provenance/recovery commands are recorded, and Layer 4 planner tests now use a vendored schema fixture instead of the live spec folder |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Cleanup branch: `codex/archive-prsg-008-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- Merge commit: `deccd8a2a9916e11edfad43df8ceef95a756dc04`
- Tree reference: `c022c26fd113bfd366da53ef6c9b1fc6392f920e`
- Pre-cleanup guard: `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` passed `66/66`
- Fixture-decoupling prerequisite: planner schema copied to `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json`

## Excluded Current Spec

None. `.specify/feature.json` is absent, and PRSG-008 is already merged.

## Provenance

- Source spec path: `specs/prsg-008-layer-planner`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/138
- Merge commit: `deccd8a2a9916e11edfad43df8ceef95a756dc04`
- Tree reference: `c022c26fd113bfd366da53ef6c9b1fc6392f920e`
- CI run URL: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27286755895
- Additional CI: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27286754549; https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27286754536
- Metadata gates: Release=pass; CodeQL=pass; PR Checks=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- Artifact manifest: `specs/prsg-008-layer-planner/SPEC-MOC.md`
- Screenshot retention: N/A
- Expiration risk: CI logs may expire; raw artifacts remain recoverable from git.

## Recovery Commands

```text
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/spec.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/plan.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/tasks.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/contracts/plan-layers.output.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/contracts/plan-layers.schema.json
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/.process/uat-runbook.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/retrospective.md
git checkout deccd8a2a9916e11edfad43df8ceef95a756dc04 -- specs/prsg-008-layer-planner
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-008 feature record |
| `.specify/memory/plan.md` | Appended implementation-plan and validation record |
| `.specify/memory/changelog.md` | Appended provenance, recovery commands, and cleanup application |
| `.specify/memory/archive-reports/2026-06-10-prsg-008-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-008 complete |
| `docs/ai/specs/.process/autopilot-state.json` | Recorded PRSG-008 archive cleanup completion |
| `AGENTS.md` | Added PRSG-008 archive cleanup note |
| `CLAUDE.md` | Removed stale active-spec plan pointer |
| `tests/speckit-pro/layer4-scripts/test-plan-layers.sh` | Repointed schema validation to vendored fixture |
| `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/` | Repointed fixtures to durable plugin files and added schema fixture |
| `specs/prsg-008-layer-planner/` | Removed from active `specs/**`; recovery commands recorded above |

## Feature Status

PRSG-008 is completed and archived. Source artifacts remain recoverable from the
merge commit.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands plus a focused test guard.

## Conflicts Resolved

- Layer 4 planner tests no longer depend on the live PRSG-008 spec schema.
- Stale agent context no longer points at `specs/prsg-008-layer-planner/plan.md`.

## Outstanding Items

None for PRSG-008 archive hygiene. PRSG-009 remains the next Phase 4 split-PR
emission spec.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/prsg-008-layer-planner`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- PRSG-008 process artifacts were not kept under active `specs/**`; recovery is
  through the merge commit commands above.
