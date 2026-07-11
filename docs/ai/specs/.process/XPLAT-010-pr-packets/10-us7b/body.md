<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/10-us7b/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 6, "deletions": 1870, "files": 64, "insertions": 1668, "merge_commits": 0, "production_files": 3, "review_order": 11, "reviewable_loc": 30, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port Layer 7 replay runners.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us9` maps this packet to T067-T072.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/09-us7..xplat-010-review/10-us7b` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/09-us7 (7584c468cbef81d60fe8bc2b911df0359c7ea243)..xplat-010-review/10-us7b (511746913f0c9bc99bd1a3245d473a029662af73)` contains 64 files, 1668 insertions, 1870 deletions, and 30 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 11 of 18.
2. Compare `xplat-010-review/09-us7` with `xplat-010-review/10-us7b` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/10-us7b` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 64 files, 1668 insertions, and 1870 deletions.
- Commit shape: 6 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 30 reviewable LOC across 3 production files and 64 total files.
- Budget result: `within_budget`.
- Changed paths:
- `.claude/claude-security-guidance.md`
- `CLAUDE.md`
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
- `docs/ai/specs/.process/XPLAT-010-workflow.md`
- `speckit-pro/speckit_pro_runner/gates/suite.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `specs/xplat-010-repository-bash-confinement/checklists/integration.md`
- `specs/xplat-010-repository-bash-confinement/plan.md`
- `specs/xplat-010-repository-bash-confinement/tasks.md`
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
- `tests/speckit-pro/layer4-scripts/test-layer7-runners.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer7-integration/README.md`
- `tests/speckit-pro/layer7-integration/dispatch-fixtures/01-clarify-codebase-only/README.md`
- `tests/speckit-pro/layer7-integration/lib/fixture_runner.py`
- `tests/speckit-pro/layer7-integration/lib/transcript-helpers.sh`
- `tests/speckit-pro/layer7-integration/reduce-transcript-fixture.sh`
- `tests/speckit-pro/layer7-integration/run-all-fixtures.py`
- `tests/speckit-pro/layer7-integration/run-all-fixtures.sh`
- `tests/speckit-pro/layer7-integration/run-dispatch-fixtures.py`
- `tests/speckit-pro/layer7-integration/run-dispatch-fixtures.sh`
- `tests/speckit-pro/layer7-integration/run-e2e-fixtures.py`
- `tests/speckit-pro/layer7-integration/run-e2e-fixtures.sh`
- `tests/speckit-pro/layer7-integration/run-grounding-fixtures.py`
- `tests/speckit-pro/layer7-integration/run-grounding-fixtures.sh`
- `tests/speckit-pro/layer7-integration/run-return-format-fixtures.py`
- `tests/speckit-pro/layer7-integration/run-return-format-fixtures.sh`
- `tests/speckit-pro/layer7-integration/scrub-transcript.sh`
- `tests/speckit-pro/parity/xplat-010/run-all-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-dispatch-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-e2e-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-grounding-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-return-format-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-layer7-runners-baseline.txt`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/09-us7` is the only immediate stack base.
- Traceability: `T067-T072` through marker `us9`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
