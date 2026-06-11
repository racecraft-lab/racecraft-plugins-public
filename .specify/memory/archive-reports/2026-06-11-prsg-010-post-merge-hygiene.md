# Archival Report: PRSG-010 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-010-harden-the-hatch` | archived in memory | cleanup applied | PRs #149-#155 are merged, provenance/recovery commands are recorded, PRSG-010 contracts are preserved under the autopilot skill payload, and focused checks passed before cleanup |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Extension invocation:
  `/speckit.archive.run specs/prsg-010-harden-the-hatch --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/149 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/150 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/151 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/152 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/153 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/154 --pr-url https://github.com/racecraft-lab/racecraft-plugins-public/pull/155 --merge-sha 8b59fe55128ee2a835c64003662ce0674cac4edf --tree-sha 08f3e8dc7cfa463a8b9e9492812bec7c1e4474a9 --metadata-gate PR-Checks=pass --metadata-gate CodeQL=pass --metadata-gate test-speckit-pro=pass --metadata-gate validate-plugins=pass --metadata-gate validate-pr-title=pass --metadata-gate detect=pass --artifact-manifest specs/prsg-010-harden-the-hatch/SPEC-MOC.md --apply-cleanup`
- Execution note: Codex executed the installed slash-command contract directly; the local `specify` CLI lists and validates installed extensions but does not expose a non-interactive subcommand to run `speckit.archive.run` directly.
- Cleanup branch: `codex/prsg-010-archive-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- PR URLs: https://github.com/racecraft-lab/racecraft-plugins-public/pull/149; https://github.com/racecraft-lab/racecraft-plugins-public/pull/150; https://github.com/racecraft-lab/racecraft-plugins-public/pull/151; https://github.com/racecraft-lab/racecraft-plugins-public/pull/152; https://github.com/racecraft-lab/racecraft-plugins-public/pull/153; https://github.com/racecraft-lab/racecraft-plugins-public/pull/154; https://github.com/racecraft-lab/racecraft-plugins-public/pull/155
- Final PR merged at: 2026-06-11T22:08:12Z
- Final merge commit: `8b59fe55128ee2a835c64003662ce0674cac4edf`
- Tree reference: `08f3e8dc7cfa463a8b9e9492812bec7c1e4474a9`
- Final PR head commit: `569b0e4cb14f4e3b958d5261a1a8ffe06704bfe6`
- Fixture-decoupling prerequisite: PRSG-010 contracts are preserved under `speckit-pro/skills/speckit-autopilot/contracts/`; final-backstop, contextual-router, O5, spec-index, and parity fixtures do not require the live spec folder.
- Pre-cleanup guards:
  - `bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh` passed `31/31`
  - `bash tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` passed `109/109`
  - `bash tests/speckit-pro/layer4-scripts/test-o5-topology.sh` passed `25/25`
  - `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` passed `87/87`
  - `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 03-prsg-010-backstop-o5-routing` passed `3/3`
- Post-cleanup verification: `bash tests/speckit-pro/run-all.sh` passed `2451/2451`

## Excluded Current Spec

None. `.specify/feature.json` is absent, and PRSG-010 is already merged.

## Provenance

- Source spec path: `specs/prsg-010-harden-the-hatch`
- PR stack:
  - #149 `fcb360280e4f3281d233741574c98b092ae29796` — scaffold and workflow foundation
  - #150 `6a9cbe2d73043c8443f550d6423a4f726caebfaa` — final backstop core
  - #151 `57c3ab24c5fd84eb880086fad21a74d0b9ec3e7c` — final hatch guidance and safety check
  - #152 `965a3ff95ed1fefdb45c93f654bc5d9594b26258` — contextual router probes
  - #153 `d29502a0e40109a3c09506f34fea6d4d3fb5dc8a` — O5 topology core
  - #154 `6d9cd5ec406fddbdbd684bf0df7add987e59f722` — O5 scaffold/status guidance
  - #155 `8b59fe55128ee2a835c64003662ce0674cac4edf` — parity, safety checks, and polish
- Metadata gates: PR Checks=pass; CodeQL=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- Artifact manifest: `specs/prsg-010-harden-the-hatch/SPEC-MOC.md`
- Task completion: 57 / 57 tasks complete
- Screenshot retention: N/A
- Expiration risk: CI logs may expire; raw artifacts remain recoverable from git.

## Recovery Commands

```text
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/spec.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/plan.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/tasks.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/research.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/data-model.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/quickstart.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/SPEC-MOC.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/final-reviewability-gate-state.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/o5-parent-manifest.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/reslicing-packet.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/routing-decision.schema.json
git checkout 8b59fe55128ee2a835c64003662ce0674cac4edf -- specs/prsg-010-harden-the-hatch
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-010 feature record |
| `.specify/memory/plan.md` | Appended implementation-plan and validation record |
| `.specify/memory/changelog.md` | Appended provenance, recovery commands, and cleanup application |
| `.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-010 complete and PRSG-012 active next |
| `docs/ai/specs/.process/autopilot-state.json` | Recorded PRSG-010 archive cleanup completion |
| `AGENTS.md` | Added PRSG-010 archive cleanup note |
| `specs/prsg-010-harden-the-hatch/` | Removed from active `specs/**`; recovery commands recorded above |

## Feature Status

PRSG-010 is completed and archived. Source artifacts remain recoverable from the
final merge commit.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands plus focused test guards.

## Conflicts Resolved

- Active status now points to PRSG-012 as the next PR-size governance spec.
- Stale post-step state no longer leaves PRSG-010 waiting at PR body generation.
- Live PRSG-010 contract paths are no longer required under active `specs/**`.

## Outstanding Items

None for PRSG-010 archive hygiene. PRSG-012 is the next PR-size governance
roadmap item.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/prsg-010-harden-the-hatch`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- PRSG-010 process artifacts were not kept under active `specs/**`; recovery is
  through the final merge commit commands above.
