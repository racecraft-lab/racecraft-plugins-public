<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/09-us7/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 5, "deletions": 211, "files": 13, "insertions": 1262, "merge_commits": 0, "production_files": 0, "review_order": 10, "reviewable_loc": 0, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port transcript helpers and tools.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us8` maps this packet to T062-T066.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/08-us6..xplat-010-review/09-us7` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/08-us6 (790b9e230de1381fda2010a22480e8594ac6628a)..xplat-010-review/09-us7 (7584c468cbef81d60fe8bc2b911df0359c7ea243)` contains 13 files, 1262 insertions, 211 deletions, and 0 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 10 of 18.
2. Compare `xplat-010-review/08-us6` with `xplat-010-review/09-us7` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/09-us7` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 13 files, 1262 insertions, and 211 deletions.
- Commit shape: 5 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 0 reviewable LOC across 0 production files and 13 total files.
- Budget result: `within_budget`.
- Changed paths:
- `.claude/claude-security-guidance.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer4-scripts/test-transcript-helpers.py`
- `tests/speckit-pro/layer4-scripts/test-transcript-helpers.sh`
- `tests/speckit-pro/layer4-scripts/test-transcript-tools.py`
- `tests/speckit-pro/layer7-integration/lib/transcript_helpers.py`
- `tests/speckit-pro/layer7-integration/reduce-transcript-fixture.py`
- `tests/speckit-pro/layer7-integration/scrub-transcript.py`
- `tests/speckit-pro/parity/xplat-010/test-transcript-helpers-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-transcript-tools-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/08-us6` is the only immediate stack base.
- Traceability: `T062-T066` through marker `us8`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
