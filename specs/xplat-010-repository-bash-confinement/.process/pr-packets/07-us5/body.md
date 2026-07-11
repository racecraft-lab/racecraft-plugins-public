<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/07-us5/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 4, "deletions": 1356, "files": 47, "insertions": 1398, "merge_commits": 0, "production_files": 3, "review_order": 8, "reviewable_loc": 68, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port toolchain and Layer 5 dispatch.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us6` maps this packet to T046-T053.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/06-us4..xplat-010-review/07-us5` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/06-us4 (cf352fbc355b30245baaf6b013166066ac4401ad)..xplat-010-review/07-us5 (c1d5e51c8ade2284629092309894b1a4a8fdb10c)` contains 47 files, 1398 insertions, 1356 deletions, and 68 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 8 of 18.
2. Compare `xplat-010-review/06-us4` with `xplat-010-review/07-us5` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/07-us5` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 47 files, 1398 insertions, and 1356 deletions.
- Commit shape: 4 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 68 reviewable LOC across 3 production files and 47 total files.
- Budget result: `within_budget`.
- Changed paths:
- `.github/workflows/pr-checks.yml`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `speckit-pro/speckit_pro_runner/gates/suite.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/check-toolchain.py`
- `tests/speckit-pro/check-toolchain.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight-docs.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-file-root.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-missing-mutable.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-missing-source-root.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-mutable.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-partial-root.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-root-mismatch.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-same-root.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-single-product.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-source-mismatch.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-stale-hash.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof-traversal-root.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache-proof.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/gates/suite.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/gates/suite.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/test-check-toolchain.py`
- `tests/speckit-pro/layer4-scripts/test-check-toolchain.sh`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- `tests/speckit-pro/parity/xplat-010/test-check-toolchain-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-pr-checks-sentinel-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/validate-tool-scoping-baseline.txt`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/06-us4` is the only immediate stack base.
- Traceability: `T046-T053` through marker `us6`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
