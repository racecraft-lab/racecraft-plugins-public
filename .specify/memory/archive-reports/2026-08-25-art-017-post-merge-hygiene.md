# Archival Report - ART-017 Arm The Accidentally-Advisory State Bookkeeping Checks

## Mode

- **archiveMode**: merged-spec cleanup, ALL sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no ART-017 run is in flight; `.specify/feature.json` is absent

## Provenance

All dates UTC.

- **Source spec path**: `specs/art-017-state-bookkeeping-checks/`
- **Workflow file**: `docs/ai/specs/.process/ART-017-workflow.md` (preserved)
- **Cleanup branch**: `archive-art017-g56r006`
- **Cleanup base**: `main` at `062d5dd94`

| PR | Title | Merged at | Merge commit |
|---|---|---|---|
| [#490](https://github.com/racecraft-lab/racecraft-plugins-public/pull/490) | `fix(art-017): Arm state bookkeeping checks` | `2026-08-23T01:58:12Z` | `070a36c2ba93da2afe1b3a49bf886c1c28903d2c` |

**The roadmap was stale by two days.** ART-017's Progress Tracking row still read
`🔄 In Progress` and the narrative above it still called the spec in progress,
although PR #490 merged on 2026-08-23. Both are reconciled here.

## Feature Summary

ART-017 armed the state bookkeeping checks that ART-014's audit found reporting
clean on input they should catch. 31/31 tasks, 20/20 functional requirements, a
same-tree 7896/7896 suite, and an independent review whose remediation reached
272/272 on the focused surface.

The defect was reproduced by execution rather than argued from reading, which is
the part worth carrying forward: three helpers returned a pass verdict on input
that violated the rule they existed to enforce.

## Acceptance Result

A user-requested manual UAT executed **all 9 acceptance scenarios**. The record
also carries the remediation of both findings its oracle raised during the run,
so it is a record of what happened rather than a checklist of what was intended.
Preserved at `docs/ai/specs/.process/ART-017-manual-uat.md`.

## Canonical Shipped Artifacts

Outside `specs/**` and unaffected:

- the armed guard and its verdicts in `speckit-pro/skills/speckit-autopilot/scripts/`
- `speckit-pro/skills/speckit-autopilot/contracts/` status-evidence contract
- `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`
- both platforms' authority documentation, generated payloads and proofs

### Historical process evidence

- `docs/ai/specs/.process/ART-017-workflow.md`
- `docs/ai/specs/.process/ART-017-manual-uat.md` (relocated)

## Evidence Relocation

| Original | Durable path | Reason |
|---|---|---|
| `.process/uat-runbook.md` | `docs/ai/specs/.process/ART-017-manual-uat.md` | executed 9-scenario acceptance record with observed results, matching the ART-005, ART-007 and G56R-005 precedent |

No retrospective exists for this spec, so none was relocated. The
`.process/pr-packets/` tree, `implementation-notes.md`, `quickstart.md`,
`research.md`, `data-model.md`, the `contracts/` and `checklists/` sets, the
`artifacts/` pages and `SPEC-MOC.md` are run exhaust for merged work and were
removed with the folder.

## Live-Reader Scan

Run before any mutation, on the bare directory name and the joined paths.

| Match | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-017-workflow.md` | historical planning paths plus the `Post: UAT Runbook Generation` row | UAT row repointed; historical paths retained as the record |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | a stale `🔄 In Progress` row and narrative | reconciled to Complete / Archived |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | a generated backlink | **regenerated**, never hand-edited |
| `tests/**`, `speckit-pro/**`, `scripts/**`, `.github/**` | **no match** | none needed |

**Nothing under `tests/` read this folder.** That is now enforced rather than
observed: `tests/speckit-pro/lib/test_result.py` fails any test reading a live
`specs/` path, shipped in PR #505.

## Recovery Commands

```text
git show 070a36c2ba93da2afe1b3a49bf886c1c28903d2c:specs/art-017-state-bookkeeping-checks/spec.md
git show 070a36c2ba93da2afe1b3a49bf886c1c28903d2c:specs/art-017-state-bookkeeping-checks/plan.md
git show 070a36c2ba93da2afe1b3a49bf886c1c28903d2c:specs/art-017-state-bookkeeping-checks/tasks.md
git show 070a36c2ba93da2afe1b3a49bf886c1c28903d2c:specs/art-017-state-bookkeeping-checks/contracts/status-evidence-guard.md
git show 070a36c2ba93da2afe1b3a49bf886c1c28903d2c:specs/art-017-state-bookkeeping-checks/.process/implementation-notes.md
```

Restore the whole folder with `git restore --source=070a36c2b --` and the path.

## Cleanup Decision

`safeToApplyCleanup=true`. PR #490 is merged, provenance and recovery commands
are recorded, no live reader remains, and the suite is green.
