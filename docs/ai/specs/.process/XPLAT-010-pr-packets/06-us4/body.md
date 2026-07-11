<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/06-us4/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 4, "deletions": 1873, "files": 20, "insertions": 2243, "merge_commits": 0, "production_files": 0, "review_order": 7, "reviewable_loc": 0, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port remaining structural checks.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us5` maps this packet to T040-T045.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/05-us3..xplat-010-review/06-us4` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/05-us3 (9b249ddd0ed0b8518006cfd404141142f7507018)..xplat-010-review/06-us4 (cf352fbc355b30245baaf6b013166066ac4401ad)` contains 20 files, 2243 insertions, 1873 deletions, and 0 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 7 of 18.
2. Compare `xplat-010-review/05-us3` with `xplat-010-review/06-us4` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/06-us4` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 20 files, 2243 insertions, and 1873 deletions.
- Commit shape: 4 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 0 reviewable LOC across 0 production files and 20 total files.
- Budget result: `within_budget`.
- Changed paths:
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `tests/speckit-pro/layer1-structural/validate-codex-skills.py`
- `tests/speckit-pro/layer1-structural/validate-codex-skills.sh`
- `tests/speckit-pro/layer1-structural/validate-moc-orphan.py`
- `tests/speckit-pro/layer1-structural/validate-moc-orphan.sh`
- `tests/speckit-pro/layer1-structural/validate-moc-stale-index.py`
- `tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh`
- `tests/speckit-pro/layer1-structural/validate-payload-conformance.py`
- `tests/speckit-pro/layer1-structural/validate-payload-conformance.sh`
- `tests/speckit-pro/layer4-scripts/test-moc-lint-exit-codes.py`
- `tests/speckit-pro/layer4-scripts/test-moc-lint-exit-codes.sh`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/parity/xplat-010/test-moc-lint-exit-codes-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-skills-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-moc-orphan-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-moc-orphan-scan-root-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-moc-stale-index-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-payload-conformance-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/05-us3` is the only immediate stack base.
- Traceability: `T040-T045` through marker `us5`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
