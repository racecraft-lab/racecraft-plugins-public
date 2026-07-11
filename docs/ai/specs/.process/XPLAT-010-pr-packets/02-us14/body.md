<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/02-us14/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 7, "deletions": 302, "files": 49, "insertions": 914, "merge_commits": 0, "production_files": 6, "review_order": 3, "reviewable_loc": 135, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Restore spec-size estimation.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us16` maps this packet to T121-T130.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/01-foundation..xplat-010-review/02-us14` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/01-foundation (1304d5a1fdbee4329d16385369a535bc2fc7a448)..xplat-010-review/02-us14 (c2d3b0c7bde975c1d7f864ce43256c60e00e44d2)` contains 49 files, 914 insertions, 302 deletions, and 135 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 3 of 18.
2. Compare `xplat-010-review/01-foundation` with `xplat-010-review/02-us14` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/02-us14` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 49 files, 914 insertions, and 302 deletions.
- Commit shape: 7 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 135 reviewable LOC across 6 production files and 49 total files.
- Budget result: `within_budget`.
- Changed paths:
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `release-please-config.json`
- `scripts/refresh-release-artifacts.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/estimate-spec-size.json`
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
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py`
- `tests/speckit-pro/layer4-scripts/test-estimate-spec-size.sh`
- `tests/speckit-pro/layer4-scripts/test-release-pr-reconciliation.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py`
- `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt`
- `tests/speckit-pro/run-all.sh`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/01-foundation` is the only immediate stack base.
- Traceability: `T121-T130` through marker `us16`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

```release-note
Restore spec-size estimation.
```
