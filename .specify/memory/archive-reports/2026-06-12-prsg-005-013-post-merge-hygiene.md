# Archival Report: PRSG-005 and PRSG-013 Post-Merge Hygiene

## Mode

- archiveMode: multi-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-005-slice-sizing-heuristics` | archived in memory | cleanup applied | PR #120 is merged, provenance/recovery commands are recorded, and shipped skill guidance plus estimator tests no longer require the live spec folder |
| `specs/prsg-013-reviewability-markers` | archived in memory | cleanup applied | PR #157 is merged, provenance/recovery commands are recorded, and PRSG-013 schemas/fixtures are preserved under the autopilot payload and test fixtures |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly; the local `specify` CLI lists and validates installed extensions but does not expose a non-interactive subcommand to run `speckit.archive.run` directly.
- Cleanup branch: `codex/spec-hygiene-prsg-013-005`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; both targets are merged and no current feature pointer is present.

## Provenance

### PRSG-005

- Source spec path: `specs/prsg-005-slice-sizing-heuristics`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/120
- Merged at: 2026-06-07T15:49:48Z
- Merge commit: `a4e930bc8989b84910b8840abb193f91bb1ae5b9`
- Tree reference: `c3dd8a196dde9f1ddb987560f7bd95573500a373`
- Final PR head commit: `6bc94585626ce0e6195f93c31acd0cf2fb86f6c5`
- Metadata gates: PR Checks=pass; CodeQL=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- Artifact manifest: `specs/prsg-005-slice-sizing-heuristics/SPEC-MOC.md`
- Task completion: 20 / 23 tasks complete; remaining Layer 2, Layer 3, and Layer 8 items were developer-local follow-up evidence, not merge blockers.

### PRSG-013

- Source spec path: `specs/prsg-013-reviewability-markers`
- PR URL: https://github.com/racecraft-lab/racecraft-plugins-public/pull/157
- Merged at: 2026-06-12T12:59:49Z
- Merge commit: `6af4e714077c8ebc9fa71466bee2461bc8652930`
- Tree reference: `d97e2bce53b322f14cf5808e86697c1bdd27c7a6`
- Final PR head commit: `cb719a078b9fa0e928ada6a7680c56f44408c06e`
- Metadata gates: PR Checks=pass; CodeQL=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass after title repair; detect=pass
- Artifact manifest: `specs/prsg-013-reviewability-markers/SPEC-MOC.md`
- Task completion: 45 / 45 tasks complete

## Verification

- `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check <repo-root>` reported `spec-index: index current`.
- `jq empty docs/ai/specs/.process/autopilot-state.json .specify/extensions/.cache/catalog.json .specify/extensions/.cache/catalog-metadata.json` passed.
- `git diff --check` passed.
- `bash tests/speckit-pro/run-all.sh` passed `2587/2587`.

## Recovery Commands

### PRSG-005

```text
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/spec.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/plan.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/tasks.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/data-model.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/quickstart.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/SPEC-MOC.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/contracts/estimate-spec-size.md
git checkout a4e930bc8989b84910b8840abb193f91bb1ae5b9 -- specs/prsg-005-slice-sizing-heuristics
```

### PRSG-013

```text
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/spec.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/plan.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/tasks.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/research.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/data-model.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/quickstart.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/SPEC-MOC.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/contracts/marker-split-result.schema.json
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/contracts/pr-marker-plan.schema.json
git checkout 6af4e714077c8ebc9fa71466bee2461bc8652930 -- specs/prsg-013-reviewability-markers
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-005 and PRSG-013 feature records |
| `.specify/memory/plan.md` | Appended implementation-plan and validation records |
| `.specify/memory/changelog.md` | Appended provenance, recovery commands, and cleanup application |
| `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added archive cleanup notes |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Added active-spec cleanup notes for PRSG-005 and PRSG-013 |
| `docs/ai/specs/.process/autopilot-state.json` | Recorded post-merge archive cleanup completion |
| `specs/prsg-005-slice-sizing-heuristics/` | Removed from active `specs/**`; recovery commands recorded above |
| `specs/prsg-013-reviewability-markers/` | Removed from active `specs/**`; recovery commands recorded above |

## Feature Status

PRSG-005 and PRSG-013 are completed and archived. Source artifacts remain
recoverable from the recorded merge commits.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands.

## Outstanding Items

- PRSG-012 remains the next ready PR-size governance implementation spec.
- PRSG-014 remains roadmap-planned optional stack-manager hardening.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/prsg-005-slice-sizing-heuristics specs/prsg-013-reviewability-markers`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- Process/workflow artifacts under `docs/ai/specs/.process/` were retained as
  project execution history.
