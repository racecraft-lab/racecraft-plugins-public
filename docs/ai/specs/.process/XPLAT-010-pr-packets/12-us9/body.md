<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/12-us9/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 4, "deletions": 1659, "files": 78, "insertions": 3326, "merge_commits": 0, "production_files": 3, "review_order": 13, "reviewable_loc": 50, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port live evaluation runners.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us11` maps this packet to T081-T087.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/11-us8..xplat-010-review/12-us9` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/11-us8 (15fac7807df11f4d8b49f9b15bbde17d304b17bf)..xplat-010-review/12-us9 (3348aa4fbb80373b39fedbd18003c63f5c33862d)` contains 78 files, 3326 insertions, 1659 deletions, and 50 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 13 of 18.
2. Compare `xplat-010-review/11-us8` with `xplat-010-review/12-us9` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/12-us9` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 78 files, 3326 insertions, and 1659 deletions.
- Commit shape: 4 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 50 reviewable LOC across 3 production files and 78 total files.
- Budget result: `within_budget`.
- Changed paths:
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
- `tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py`
- `tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.sh`
- `tests/speckit-pro/layer2-trigger/run-trigger-evals.py`
- `tests/speckit-pro/layer2-trigger/run-trigger-evals.sh`
- `tests/speckit-pro/layer2-trigger/run-trigger-loop.py`
- `tests/speckit-pro/layer2-trigger/run-trigger-loop.sh`
- `tests/speckit-pro/layer3-functional/run-functional-evals-codex.py`
- `tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh`
- `tests/speckit-pro/layer3-functional/run-functional-evals.py`
- `tests/speckit-pro/layer3-functional/run-functional-evals.sh`
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
- `tests/speckit-pro/layer4-scripts/test-eval-runner-skill-selection.py`
- `tests/speckit-pro/layer4-scripts/test-eval-runner-skill-selection.sh`
- `tests/speckit-pro/layer4-scripts/test-l6-codex-runner.py`
- `tests/speckit-pro/layer4-scripts/test-l6-codex-runner.sh`
- `tests/speckit-pro/layer4-scripts/test-layer2-signal-restoration.py`
- `tests/speckit-pro/layer4-scripts/test-layer2-trigger-runners.py`
- `tests/speckit-pro/layer4-scripts/test-layer6-portability.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer6-efficiency/fixtures-codex/README.md`
- `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py`
- `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.sh`
- `tests/speckit-pro/layer6-efficiency/lib/token-counter.py`
- `tests/speckit-pro/layer6-efficiency/lib/token-counter.sh`
- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`
- `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.sh`
- `tests/speckit-pro/parity/xplat-010/quality-scorer-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-efficiency-benchmarks-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-functional-evals-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-functional-evals-codex-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-trigger-evals-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-trigger-evals-codex-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/run-trigger-loop-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-eval-runner-skill-selection-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-l6-codex-runner-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-layer2-signal-restoration-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-layer2-trigger-runners-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-layer6-portability-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/token-counter-baseline.txt`
- `tests/speckit-pro/run-all.py`
- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/test-run-all.py`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/11-us8` is the only immediate stack base.
- Traceability: `T081-T087` through marker `us11`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
