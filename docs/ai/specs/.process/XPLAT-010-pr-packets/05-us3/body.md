<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/05-us3/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 4, "deletions": 1597, "files": 37, "insertions": 2429, "merge_commits": 0, "production_files": 1, "review_order": 6, "reviewable_loc": 2, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port structural validator batch two.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us4` maps this packet to T029-T039.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/04-us2..xplat-010-review/05-us3` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/04-us2 (7d6a6d115b6832e3f61e7e25701292679b9079d3)..xplat-010-review/05-us3 (9b249ddd0ed0b8518006cfd404141142f7507018)` contains 37 files, 2429 insertions, 1597 deletions, and 2 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 6 of 18.
2. Compare `xplat-010-review/04-us2` with `xplat-010-review/05-us3` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/05-us3` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 37 files, 2429 insertions, and 1597 deletions.
- Commit shape: 4 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 2 reviewable LOC across 1 production files and 37 total files.
- Budget result: `within_budget`.
- Changed paths:
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference/source-vs-dist.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `tests/speckit-pro/layer1-structural/validate-payload-completeness.py`
- `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh`
- `tests/speckit-pro/layer1-structural/validate-plugin-payload.py`
- `tests/speckit-pro/layer1-structural/validate-plugin-payload.sh`
- `tests/speckit-pro/layer1-structural/validate-plugin.py`
- `tests/speckit-pro/layer1-structural/validate-plugin.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
- `tests/speckit-pro/layer1-structural/validate-process-gitattributes.py`
- `tests/speckit-pro/layer1-structural/validate-process-gitattributes.sh`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.py`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.sh`
- `tests/speckit-pro/layer1-structural/validate-scripts.py`
- `tests/speckit-pro/layer1-structural/validate-scripts.sh`
- `tests/speckit-pro/layer1-structural/validate-skill-capability-pointers.py`
- `tests/speckit-pro/layer1-structural/validate-skill-capability-pointers.sh`
- `tests/speckit-pro/layer1-structural/validate-skills.py`
- `tests/speckit-pro/layer1-structural/validate-skills.sh`
- `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.py`
- `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.sh`
- `tests/speckit-pro/layer4-scripts/test-layer1-validator-regressions.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/parity/xplat-010/validate-payload-completeness-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-plugin-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-plugin-payload-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-pr-checks-sentinel-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-process-gitattributes-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-release-workflow-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-scripts-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-skill-capability-pointers-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-skills-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-spec-index-determinism-baseline.txt`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/04-us2` is the only immediate stack base.
- Traceability: `T029-T039` through marker `us4`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
