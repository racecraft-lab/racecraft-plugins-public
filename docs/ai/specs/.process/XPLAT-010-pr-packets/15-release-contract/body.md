<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/15-release-contract/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 5, "deletions": 31, "files": 26, "insertions": 1831, "merge_commits": 0, "production_files": 1, "review_order": 16, "reviewable_loc": 546, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Validate consumer release-note blocks.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us14` maps this packet to T109-T112.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/14-us11..xplat-010-review/15-release-contract` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/14-us11 (c6b47a6d8587f4a1b841f3d52bc8ba933794ac98)..xplat-010-review/15-release-contract (b3c81e25fae0e00b52a4cc95c681322630af592f)` contains 26 files, 1831 insertions, 31 deletions, and 546 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 16 of 18.
2. Compare `xplat-010-review/14-us11` with `xplat-010-review/15-release-contract` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/15-release-contract` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 26 files, 1831 insertions, and 31 deletions.
- Commit shape: 5 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 546 reviewable LOC across 1 production files and 26 total files.
- Budget result: `warning`.
- Changed paths:
- `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/release-note-block.contract.md`
- `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/release-note-block.contract.md`
- `docs-site/src/content/docs/reference/scripts.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `scripts/release_note_policy.py`
- `speckit-pro/skills/speckit-autopilot/contracts/release-note-block.contract.md`
- `tests/speckit-pro/parity/bash-to-python/test-release-note-policy-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/contracts/release-note-block.contract.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/contracts/release-note-block.contract.md`
- `tests/speckit-pro/unit/test-release-note-policy.py`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/14-us11` is the only immediate stack base.
- Traceability: `T109-T112` through marker `us14`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Required-check callout: branch protection does not currently require `validate-release-note`. After the workflow lands, a repository administrator must add that exact check in Settings -> Branches and record the resulting configuration evidence; this packet does not claim that operator action is complete.

## Release note

```release-note
Validate consumer release-note blocks.
```
