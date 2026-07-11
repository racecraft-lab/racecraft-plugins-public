<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/14-us11/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 10, "deletions": 114, "files": 22, "insertions": 3632, "merge_commits": 0, "production_files": 1, "review_order": 15, "reviewable_loc": 1, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Add Linux and Windows runner checks.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us13` maps this packet to T100-T108.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/13-us10..xplat-010-review/14-us11` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/13-us10 (93aaddd09d04a89b60bdc0085073a732b95e705c)..xplat-010-review/14-us11 (c6b47a6d8587f4a1b841f3d52bc8ba933794ac98)` contains 22 files, 3632 insertions, 114 deletions, and 1 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 15 of 18.
2. Compare `xplat-010-review/13-us10` with `xplat-010-review/14-us11` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/14-us11` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 22 files, 3632 insertions, and 114 deletions.
- Commit shape: 10 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 1 reviewable LOC across 1 production files and 22 total files.
- Budget result: `within_budget`.
- Changed paths:
- `.gitattributes`
- `.github/workflows/container-preflight.yml`
- `CLAUDE.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-design-concept.md`
- `docs/ai/specs/.process/XPLAT-010-workflow.md`
- `specs/xplat-010-repository-bash-confinement/checklists/reliability.md`
- `specs/xplat-010-repository-bash-confinement/checklists/requirements.md`
- `specs/xplat-010-repository-bash-confinement/checklists/security.md`
- `specs/xplat-010-repository-bash-confinement/data-model.md`
- `specs/xplat-010-repository-bash-confinement/spec.md`
- `specs/xplat-010-repository-bash-confinement/tasks.md`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`
- `tests/speckit-pro/layer1-structural/workflow_yaml_sanity.py`
- `tests/speckit-pro/parity/bash-to-python/validate-pr-checks-sentinel-baseline.txt`
- `tests/speckit-pro/run-container-preflight.py`
- `tests/speckit-pro/run-hosted-windows-preflight.py`
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/unit/test-hosted-windows-preflight.py`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- `tests/speckit-pro/unit/test-structural-validator-regressions.py`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/13-us10` is the only immediate stack base.
- Traceability: `T100-T108` through marker `us13`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted pull-request checks are evidence for the pre-merge path only. After this workflow exists on `main`, an operator must run its `workflow_dispatch` path and record the Linux, advisory Windows, ARM64-disabled, sentinel, and artifact results.

## Release note

Not required for this Conventional Commit type.
