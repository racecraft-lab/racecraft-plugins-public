<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/03-us1/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 6, "deletions": 694, "files": 49, "insertions": 2439, "merge_commits": 0, "production_files": 4, "review_order": 4, "reviewable_loc": 105, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Replace Bash suite orchestration with Python.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us2` maps this packet to T008-T017.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/02-us14..xplat-010-review/03-us1` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/02-us14 (c2d3b0c7bde975c1d7f864ce43256c60e00e44d2)..xplat-010-review/03-us1 (9f9684fa6fa48d70dc0053f96e2b253435ecdf57)` contains 49 files, 2439 insertions, 694 deletions, and 105 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 4 of 18.
2. Compare `xplat-010-review/02-us14` with `xplat-010-review/03-us1` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/03-us1` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 49 files, 2439 insertions, and 694 deletions.
- Commit shape: 6 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 105 reviewable LOC across 4 production files and 49 total files.
- Budget result: `within_budget`.
- Changed paths:
- `dist/claude/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference/source-vs-dist.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md`
- `speckit-pro/speckit_pro_runner/gates/suite.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
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
- `tests/speckit-pro/layer4-scripts/test-capture-python-baseline.py`
- `tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`
- `tests/speckit-pro/lib/capture_baseline.py`
- `tests/speckit-pro/lib/capture_python_baseline.py`
- `tests/speckit-pro/lib/test_lib.py`
- `tests/speckit-pro/lib/test_result.py`
- `tests/speckit-pro/run-all.py`
- `tests/speckit-pro/run-all.sh`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/test-run-all.py`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/02-us14` is the only immediate stack base.
- Traceability: `T008-T017` through marker `us2`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

```release-note
Replace Bash suite orchestration with Python.
```
