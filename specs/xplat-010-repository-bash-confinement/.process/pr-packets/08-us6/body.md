<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/08-us6/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 2, "deletions": 1511, "files": 24, "insertions": 1917, "merge_commits": 0, "production_files": 9, "review_order": 9, "reviewable_loc": 1392, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port repository helpers and hooks.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us7` maps this packet to T054-T061.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/07-us5..xplat-010-review/08-us6` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/07-us5 (c1d5e51c8ade2284629092309894b1a4a8fdb10c)..xplat-010-review/08-us6 (790b9e230de1381fda2010a22480e8594ac6628a)` contains 24 files, 1917 insertions, 1511 deletions, and 1392 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 9 of 18.
2. Compare `xplat-010-review/07-us5` with `xplat-010-review/08-us6` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/08-us6` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 24 files, 1917 insertions, and 1511 deletions.
- Commit shape: 2 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 1392 reviewable LOC across 9 production files and 24 total files.
- Budget result: `exception`.
- Changed paths:
- `.claude/hooks/guard-version-triplet.py`
- `.claude/hooks/guard-version-triplet.sh`
- `.claude/hooks/validate-structural.py`
- `.claude/hooks/validate-structural.sh`
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference/scripts.md`
- `docs-site/src/content/docs/reference/source-vs-dist.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `scripts/refresh-local-plugin.py`
- `scripts/refresh-local-plugin.sh`
- `scripts/sync-marketplace-versions.py`
- `scripts/sync-marketplace-versions.sh`
- `tests/speckit-pro/layer4-scripts/test-claude-hooks.py`
- `tests/speckit-pro/layer4-scripts/test-refresh-local-plugin.py`
- `tests/speckit-pro/layer4-scripts/test-refresh-local-plugin.sh`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer4-scripts/test-sync-marketplace-versions.py`
- `tests/speckit-pro/layer4-scripts/test-sync-marketplace-versions.sh`
- `tests/speckit-pro/parity/xplat-010/test-claude-hooks-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-refresh-local-plugin-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-sync-marketplace-versions-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-sync-marketplace-versions-bash-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/07-us5` is the only immediate stack base.
- Traceability: `T054-T061` through marker `us7`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
