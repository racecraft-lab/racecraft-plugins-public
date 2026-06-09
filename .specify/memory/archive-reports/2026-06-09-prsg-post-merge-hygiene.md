# Archival Report: PRSG Post-Merge Hygiene

## Mode

- archiveMode: sweep
- dryRun: true
- applyCleanupRequested: false
- dryRunProvenanceOnly: true
- safeToApplyCleanup: false

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-007-atomicity-router` | archived in memory | retain active folder | PR #133 is merged and provenance is recorded, but Layer 4 dogfood/schema tests read the live folder |
| `specs/prsg-011-retro-migration` | archived in memory | retain active folder | PR #132 is merged and provenance is recorded; cleanup deferred so PRSG cleanup can happen as one test-safe change |

## Excluded Current Spec

None. The stale `.specify/feature.json` pointer to PRSG-011 was removed because
PRSG-011 is already merged.

## Provenance

### PRSG-007

- Source spec path: `specs/prsg-007-atomicity-router`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/133
- Merge commit: `c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6`
- CI run URL: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27214328113
- Metadata gates: validate-plugins=pass; test(speckit-pro)=pass; validate-pr-title=pass; detect=pass; CodeQL=pass
- Artifact manifest: `specs/prsg-007-atomicity-router/SPEC-MOC.md`
- Screenshot retention: N/A
- Expiration risk: CI logs may expire; raw artifacts remain recoverable from git.

### PRSG-011

- Source spec path: `specs/prsg-011-retro-migration`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/132
- Merge commit: `6916ec43d2d4e3972d7e12425a05158f0b48ae3b`
- CI run URL: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27210286401
- Metadata gates: validate-plugins=pass; test(speckit-pro)=pass; detect=pass; CodeQL=pass; validate-pr-title=fail on merged title
- Artifact manifest: `specs/prsg-011-retro-migration/SPEC-MOC.md`
- Screenshot retention: N/A
- Expiration risk: CI logs may expire; raw artifacts remain recoverable from git.

## Recovery Commands

```text
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/spec.md
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/plan.md
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/tasks.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/spec.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/plan.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/tasks.md
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-007 and PRSG-011 feature records |
| `.specify/memory/plan.md` | Appended implementation-plan and verification records |
| `.specify/memory/changelog.md` | Appended provenance and recovery commands |
| `AGENTS.md` | Added cleanup caution for PRSG-007 and transient feature pointer |
| `.specify/extensions/archive/RACECRAFT-PIN.md` | Recorded archive extension source, tag, commit, and manifest hash |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-007 and PRSG-011 complete |
| `docs/ai/specs/.process/autopilot-state.json` | Refreshed latest completed workflow pointer to PRSG-007 / PR #133 |
| `.specify/feature.json` | Removed stale completed-spec pointer |

## Cleanup Decision

- cleanupApplied: false
- cleanupCommand: N/A
- blockedBy: PRSG-007 live spec directory is still used by Layer 4 dogfood/schema tests

## Defaults Applied

- No docs-side `.process` files were deleted.
- No active `specs/**` folder was removed.
- Cleanup can be revisited after tests are decoupled from live archived spec dirs.
