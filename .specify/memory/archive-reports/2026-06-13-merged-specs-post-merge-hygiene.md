# Archival Report: Merged Specs Post-Merge Hygiene

## Mode

- archiveMode: multi-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/001-repository-foundation` | merged | cleanup applied | PR #1 is merged, provenance/recovery commands are recorded, and release-please/marketplace sync behavior lives in production files and tests |
| `specs/002-pr-checks-workflow` | merged | cleanup applied | PR #2 is merged, provenance/recovery commands are recorded, and PR checks workflow behavior lives in `.github/workflows/pr-checks.yml` |
| `specs/003-release-automation` | merged | cleanup applied | PR #3 is merged, provenance/recovery commands are recorded, and release workflow behavior lives in `.github/workflows/release.yml` |
| `specs/004-integration-verification` | merged | cleanup applied | PR #5 is merged; its stale unchecked task ledger is recorded as historical inconsistency rather than retained as an active spec |
| `specs/006a-uat-skeleton` | merged | cleanup applied | PR #99 is merged, the full-spec test dependency was already vendored as `tests/speckit-pro/layer4-scripts/fixtures/spec-full-snapshot.md`, and recovery commands are recorded |
| `specs/prsg-002-moc-templates` | merged | cleanup applied | PR #116 is merged, MOC lint dogfood assertions now use committed fixtures, and recovery commands are recorded |
| `specs/prsg-003-spec-index` | merged | cleanup applied | PR #121 is merged, generator behavior is covered by committed fixtures, and recovery commands are recorded |
| `specs/prsg-004-roadmap-moc-home-note` | merged | cleanup applied | PR #129 is merged, one PR-review-packet task remained unchecked but was not a merge blocker, and recovery commands are recorded |
| `specs/prsg-006-reviewability-budget` | merged | cleanup applied | PR #119 is merged, estimator/gate behavior lives in production scripts plus tests, and recovery commands are recorded |
| `specs/prsg-012-reviewer-ready-pr-packet-contract` | merged | cleanup applied | PR stack #164-#168 is merged, PRSG-012 test dependencies were vendored under `tests/`, and recovery commands are recorded |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly; the local `specify` CLI lists and validates installed extensions but does not expose a non-interactive subcommand to run `speckit.archive.run` directly.
- Cleanup branch: `codex/archive-merged-specs-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; all active `specs/**` folders were verified as merged or already historical.

## Fixture-Decoupling Prerequisites

- `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` now seeds PRSG-012 packet-generation tests from `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/`.
- `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` now reads PRSG-012 marker-plan regression fixtures from `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/`.
- `tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` and `validate-moc-orphan.sh` now use committed MOC fixtures for the former PRSG-002 dogfood assertions.
- The SPEC-006a UAT full-spec snapshot was already vendored at `tests/speckit-pro/layer4-scripts/fixtures/spec-full-snapshot.md`.

## Provenance

| Spec | PR | Merged at | Merge commit | Tree reference | Task completion |
|------|----|-----------|--------------|----------------|-----------------|
| `specs/001-repository-foundation` | #1 | 2026-04-02T02:14:51Z | `b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2` | `0bc6ef47bf24f37f63a8a3effec2b533ca93c2ef` | 30 / 30 |
| `specs/002-pr-checks-workflow` | #2 | 2026-04-02T04:17:52Z | `030c47a6ae7f032d96a158883b4b6bfde2f5ef19` | `2143519cda2908838e8e1b3f5689b4233c9eccea` | 16 / 16 |
| `specs/003-release-automation` | #3 | 2026-04-02T04:30:50Z | `5a52abebf05941eca0905e2ba61b0b9e66b374c1` | `2468efe7e9d400080acdf38fb4fd1af62b40322e` | 11 / 11 |
| `specs/004-integration-verification` | #5 | 2026-04-04T12:45:49Z | `c11d9291a13b984cfca467a3418ac482e566c49b` | `acd61703cfd47e129c43d7895a848cf11e36623b` | 0 / 31 recorded; merged PR is authoritative |
| `specs/006a-uat-skeleton` | #99 | 2026-05-29T16:13:06Z | `dcd1208a57780abbb9c9d204b3c096be3a7da188` | `df5f8a07aae0005185f82e557994e592edd3872d` | 28 / 28 |
| `specs/prsg-002-moc-templates` | #116 | 2026-06-07T01:20:56Z | `3e4be3e9901c466040809a211af8aa0ec0c6935b` | `c6cc7c63dabce308d1a15552872ca7958564f25d` | 24 / 24 |
| `specs/prsg-003-spec-index` | #121 | 2026-06-07T15:42:06Z | `339fbaadc299f3593392937cf563b33e5d44627a` | `6cbdf0e7279c39641d9249524cb209a44d41e2df` | 25 / 25 |
| `specs/prsg-004-roadmap-moc-home-note` | #129 | 2026-06-08T22:31:50Z | `60018313eb768b8339cf60737e9b9965cc9465b8` | `1bf3942b2c88fdb959cf6c54001b82c1c402feef` | 23 / 24; remaining PR packet task was not a merge blocker |
| `specs/prsg-006-reviewability-budget` | #119 | 2026-06-07T15:59:03Z | `9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53` | `8f0058ff12832c0c08529cdf97295eba20cd9954` | 35 / 35 |
| `specs/prsg-012-reviewer-ready-pr-packet-contract` | #164-#168 | 2026-06-13T00:15:01Z final | `896ab42f443e330d095f1c08be681cc8c9bca995` | `4c50790bf3009149c07eeba92771f5b2a501995d` | 56 / 56 |

### PRSG-012 Stack

| PR | Merge commit | Scope |
|----|--------------|-------|
| #164 | `b57e2992b8e304b0e649398b86f7b495aada3252` | Add reviewer packet validation contract |
| #165 | `7580f08fc78877f21a71c72ff4a6a2781c9017ce` | Generate packet-owned conventional PR titles |
| #166 | `d6685c44ae706370ec91977831d3d1149c299b65` | Render plain-English reviewer PR body evidence |
| #167 | `302d73a884d7fbe10964839f17460aec91f04dc1` | Block invalid PR packets before creation |
| #168 | `896ab42f443e330d095f1c08be681cc8c9bca995` | Protect editable PR body prose |

## Pre-Cleanup Verification

- `bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` passed `85/85`.
- `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` passed `156/156`.
- `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` passed `11/11`.
- `bash tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` passed `29/29`.

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated `docs/ai/specs/interactive-documentation-roadmap-MOC.md`.
- `bash tests/speckit-pro/run-all.sh` passed `2915/2915`.
  - Layer 1 structural: `549/549`.
  - Layer 1 Codex structural: `430/430`.
  - Layer 4 script unit: `1746/1746`.
  - Layer 5 tool scoping: `190/190`.

## Recovery Commands

### SPEC-001

```text
git show b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2:specs/001-repository-foundation/spec.md
git show b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2:specs/001-repository-foundation/plan.md
git show b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2:specs/001-repository-foundation/tasks.md
git checkout b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2 -- specs/001-repository-foundation
```

### SPEC-002

```text
git show 030c47a6ae7f032d96a158883b4b6bfde2f5ef19:specs/002-pr-checks-workflow/spec.md
git show 030c47a6ae7f032d96a158883b4b6bfde2f5ef19:specs/002-pr-checks-workflow/plan.md
git show 030c47a6ae7f032d96a158883b4b6bfde2f5ef19:specs/002-pr-checks-workflow/tasks.md
git checkout 030c47a6ae7f032d96a158883b4b6bfde2f5ef19 -- specs/002-pr-checks-workflow
```

### SPEC-003

```text
git show 5a52abebf05941eca0905e2ba61b0b9e66b374c1:specs/003-release-automation/spec.md
git show 5a52abebf05941eca0905e2ba61b0b9e66b374c1:specs/003-release-automation/plan.md
git show 5a52abebf05941eca0905e2ba61b0b9e66b374c1:specs/003-release-automation/tasks.md
git checkout 5a52abebf05941eca0905e2ba61b0b9e66b374c1 -- specs/003-release-automation
```

### SPEC-004

```text
git show c11d9291a13b984cfca467a3418ac482e566c49b:specs/004-integration-verification/spec.md
git show c11d9291a13b984cfca467a3418ac482e566c49b:specs/004-integration-verification/plan.md
git show c11d9291a13b984cfca467a3418ac482e566c49b:specs/004-integration-verification/tasks.md
git checkout c11d9291a13b984cfca467a3418ac482e566c49b -- specs/004-integration-verification
```

### SPEC-006a

```text
git show dcd1208a57780abbb9c9d204b3c096be3a7da188:specs/006a-uat-skeleton/spec.md
git show dcd1208a57780abbb9c9d204b3c096be3a7da188:specs/006a-uat-skeleton/plan.md
git show dcd1208a57780abbb9c9d204b3c096be3a7da188:specs/006a-uat-skeleton/tasks.md
git show dcd1208a57780abbb9c9d204b3c096be3a7da188:specs/006a-uat-skeleton/uat-runbook.md
git checkout dcd1208a57780abbb9c9d204b3c096be3a7da188 -- specs/006a-uat-skeleton
```

### PRSG-002

```text
git show 3e4be3e9901c466040809a211af8aa0ec0c6935b:specs/prsg-002-moc-templates/spec.md
git show 3e4be3e9901c466040809a211af8aa0ec0c6935b:specs/prsg-002-moc-templates/plan.md
git show 3e4be3e9901c466040809a211af8aa0ec0c6935b:specs/prsg-002-moc-templates/tasks.md
git show 3e4be3e9901c466040809a211af8aa0ec0c6935b:specs/prsg-002-moc-templates/SPEC-MOC.md
git checkout 3e4be3e9901c466040809a211af8aa0ec0c6935b -- specs/prsg-002-moc-templates
```

### PRSG-003

```text
git show 339fbaadc299f3593392937cf563b33e5d44627a:specs/prsg-003-spec-index/spec.md
git show 339fbaadc299f3593392937cf563b33e5d44627a:specs/prsg-003-spec-index/plan.md
git show 339fbaadc299f3593392937cf563b33e5d44627a:specs/prsg-003-spec-index/tasks.md
git show 339fbaadc299f3593392937cf563b33e5d44627a:specs/prsg-003-spec-index/SPEC-MOC.md
git checkout 339fbaadc299f3593392937cf563b33e5d44627a -- specs/prsg-003-spec-index
```

### PRSG-004

```text
git show 60018313eb768b8339cf60737e9b9965cc9465b8:specs/prsg-004-roadmap-moc-home-note/spec.md
git show 60018313eb768b8339cf60737e9b9965cc9465b8:specs/prsg-004-roadmap-moc-home-note/plan.md
git show 60018313eb768b8339cf60737e9b9965cc9465b8:specs/prsg-004-roadmap-moc-home-note/tasks.md
git checkout 60018313eb768b8339cf60737e9b9965cc9465b8 -- specs/prsg-004-roadmap-moc-home-note
```

### PRSG-006

```text
git show 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53:specs/prsg-006-reviewability-budget/spec.md
git show 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53:specs/prsg-006-reviewability-budget/plan.md
git show 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53:specs/prsg-006-reviewability-budget/tasks.md
git checkout 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53 -- specs/prsg-006-reviewability-budget
```

### PRSG-012

```text
git show 896ab42f443e330d095f1c08be681cc8c9bca995:specs/prsg-012-reviewer-ready-pr-packet-contract/spec.md
git show 896ab42f443e330d095f1c08be681cc8c9bca995:specs/prsg-012-reviewer-ready-pr-packet-contract/plan.md
git show 896ab42f443e330d095f1c08be681cc8c9bca995:specs/prsg-012-reviewer-ready-pr-packet-contract/tasks.md
git show 896ab42f443e330d095f1c08be681cc8c9bca995:specs/prsg-012-reviewer-ready-pr-packet-contract/SPEC-MOC.md
git show 896ab42f443e330d095f1c08be681cc8c9bca995:specs/prsg-012-reviewer-ready-pr-packet-contract/contracts/pr-packet.schema.json
git checkout 896ab42f443e330d095f1c08be681cc8c9bca995 -- specs/prsg-012-reviewer-ready-pr-packet-contract
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled feature records for the merged active spec folders |
| `.specify/memory/plan.md` | Appended implementation-plan and validation records for the cleanup sweep |
| `.specify/memory/changelog.md` | Appended provenance, recovery commands, and cleanup application |
| `.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added archive cleanup notes for all newly removed merged spec folders |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-012 complete and active-spec cleanup applied |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Regenerated active SPEC index after merged spec cleanup |
| `specs/.gitkeep` | Kept the active specs root present while containing no active spec folders |
| `tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` | Replaced live PRSG-002 dogfood dependency with committed fixture assertions |
| `tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh` | Replaced live PRSG-002 dogfood dependency with committed fixture assertions |
| `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` | Replaced live PRSG-012 feature dependency with a committed fixture |
| `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` | Replaced live PRSG-012 marker-plan dependency with committed fixtures |
| `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh` | Replaced live PRSG-012 feature dependency with a committed fixture |
| `tests/speckit-pro/layer4-scripts/fixtures/` | Added fixture-backed PRSG-012 feature and marker-plan snapshots |
| `specs/*` | Removed merged active spec folders listed in the sweep summary |

## Feature Status

All listed specs are completed or historically merged and archived. Source
artifacts remain recoverable from the recorded merge commits.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands plus fixture decoupling for live-spec test dependencies.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/001-repository-foundation specs/002-pr-checks-workflow specs/003-release-automation specs/004-integration-verification specs/006a-uat-skeleton specs/prsg-002-moc-templates specs/prsg-003-spec-index specs/prsg-004-roadmap-moc-home-note specs/prsg-006-reviewability-budget specs/prsg-012-reviewer-ready-pr-packet-contract`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- Historical workflow/process artifacts under `docs/ai/specs/` and `docs/ai/specs/.process/` were retained as project execution history.
- PRSG-012 live branch refs were not used for recovery because the merged stack branches were pruned; merge commits are the recovery authority.
