<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/04-us2/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 2, "deletions": 1468, "files": 34, "insertions": 2110, "merge_commits": 0, "production_files": 1, "review_order": 5, "reviewable_loc": 2, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port structural validator batch one.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us3` maps this packet to T018-T028.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/03-us1..xplat-010-review/04-us2` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/03-us1 (9f9684fa6fa48d70dc0053f96e2b253435ecdf57)..xplat-010-review/04-us2 (7d6a6d115b6832e3f61e7e25701292679b9079d3)` contains 34 files, 2110 insertions, 1468 deletions, and 2 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 5 of 18.
2. Compare `xplat-010-review/03-us1` with `xplat-010-review/04-us2` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/04-us2` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 34 files, 2110 insertions, and 1468 deletions.
- Commit shape: 2 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 2 reviewable LOC across 1 production files and 34 total files.
- Budget result: `within_budget`.
- Changed paths:
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `tests/speckit-pro/layer1-structural/validate-agents.py`
- `tests/speckit-pro/layer1-structural/validate-agents.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-pointer.py`
- `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-resolution.py`
- `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.py`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.sh`
- `tests/speckit-pro/layer1-structural/validate-codex-hooks.py`
- `tests/speckit-pro/layer1-structural/validate-codex-hooks.sh`
- `tests/speckit-pro/layer1-structural/validate-codex-marketplace.py`
- `tests/speckit-pro/layer1-structural/validate-codex-marketplace.sh`
- `tests/speckit-pro/layer1-structural/validate-codex-parity.py`
- `tests/speckit-pro/layer1-structural/validate-codex-parity.sh`
- `tests/speckit-pro/layer1-structural/validate-codex-plugin.py`
- `tests/speckit-pro/layer1-structural/validate-codex-plugin.sh`
- `tests/speckit-pro/layer1-structural/validate-curated-set.py`
- `tests/speckit-pro/layer1-structural/validate-curated-set.sh`
- `tests/speckit-pro/layer1-structural/validate-hooks.py`
- `tests/speckit-pro/layer1-structural/validate-hooks.sh`
- `tests/speckit-pro/parity/xplat-010/validate-agents-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-capability-pointer-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-capability-resolution-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-agents-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-hooks-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-marketplace-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-parity-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-codex-plugin-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-curated-set-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-hooks-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/03-us1` is the only immediate stack base.
- Traceability: `T018-T028` through marker `us3`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
