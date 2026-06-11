# Archival Report: PRSG-009 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-009-multi-pr-emission` | archived in memory | cleanup applied | PR #145 is merged, provenance/recovery commands are recorded, PRSG-009 contracts are preserved under the autopilot skill payload, and focused/full tests pass without the live spec folder |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Cleanup branch: `codex/prsg-009-archive-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/145
- PR merged at: 2026-06-11T14:00:38Z
- Merge commit: `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`
- Tree reference: `c65ad8ae716d3f8cae94ac28026159eebd12a101`
- Final PR head commit: `74fb0eecec0b3bda8c0c180dddc025cbdd2d2f4a`
- Fixture-decoupling prerequisite: PRSG-009 contracts preserved under `speckit-pro/skills/speckit-autopilot/contracts/`, and `multi-pr-emission.sh` now reports payload-included contract paths.
- Pre-cleanup guards:
  - `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` passed `81/81`
  - `bash tests/speckit-pro/layer4-scripts/test-restack.sh` passed `32/32`
  - `bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` passed `44/44`
  - `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` passed `86/86`
- Post-cleanup verification: `bash tests/speckit-pro/run-all.sh` passed `2300/2300`

## Excluded Current Spec

None. `.specify/feature.json` is absent, and PRSG-009 is already merged.

## Provenance

- Source spec path: `specs/prsg-009-multi-pr-emission`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/145
- Merge commit: `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`
- Tree reference: `c65ad8ae716d3f8cae94ac28026159eebd12a101`
- PR Checks run URL: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351131255
- Release run URL: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27352284669
- CodeQL run URLs: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351042365; https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351042214; https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27352282130
- Metadata gates: Release=pass; CodeQL=pass; PR Checks=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- Artifact manifest: `specs/prsg-009-multi-pr-emission/SPEC-MOC.md`
- Task completion: 47 / 47 tasks complete
- Screenshot retention: N/A
- Expiration risk: CI logs may expire; raw artifacts remain recoverable from git.

## Recovery Commands

```text
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/spec.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/plan.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/tasks.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/multi-pr-emission-state.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/prs-v2.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/restack-output.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/slice-packet.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/.process/uat-runbook.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/retrospective.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/verify-tasks-report.md
git checkout a3361d50e3dfc5463fb2d5dbb2737a3525637a32 -- specs/prsg-009-multi-pr-emission
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-009 feature record |
| `.specify/memory/plan.md` | Appended implementation-plan and validation record |
| `.specify/memory/changelog.md` | Appended provenance, recovery commands, and cleanup application |
| `.specify/memory/archive-reports/2026-06-11-prsg-009-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-009 complete |
| `docs/ai/specs/.process/autopilot-state.json` | Recorded PRSG-009 archive cleanup completion |
| `AGENTS.md` | Added PRSG-009 archive cleanup note |
| `CLAUDE.md` | Removed stale active-spec plan pointer |
| `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` | Repointed schema path reporting to payload-included contracts |
| `speckit-pro/skills/speckit-autopilot/contracts/` | Added durable PRSG-009 contract schemas |
| `specs/prsg-009-multi-pr-emission/` | Removed from active `specs/**`; recovery commands recorded above |

## Feature Status

PRSG-009 is completed and archived. Source artifacts remain recoverable from the
merge commit.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands plus focused and full test guards.

## Conflicts Resolved

- Layer 4 PRSG-009 contract paths no longer depend on the live spec directory.
- Stale agent context no longer points at `specs/prsg-009-multi-pr-emission/plan.md`.

## Outstanding Items

None for PRSG-009 archive hygiene. PRSG-010 remains the next PR-size governance
roadmap item.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/prsg-009-multi-pr-emission`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- PRSG-009 process artifacts were not kept under active `specs/**`; recovery is
  through the merge commit commands above.
