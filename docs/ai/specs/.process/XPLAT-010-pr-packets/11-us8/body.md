<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/11-us8/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 6, "deletions": 1246, "files": 76, "insertions": 2345, "merge_commits": 0, "production_files": 3, "review_order": 12, "reviewable_loc": 30, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Port Layer 8 parity harness.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us10` maps this packet to T073-T080.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/10-us7b..xplat-010-review/11-us8` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/10-us7b (511746913f0c9bc99bd1a3245d473a029662af73)..xplat-010-review/11-us8 (15fac7807df11f4d8b49f9b15bbde17d304b17bf)` contains 76 files, 2345 insertions, 1246 deletions, and 30 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 12 of 18.
2. Compare `xplat-010-review/10-us7b` with `xplat-010-review/11-us8` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/11-us8` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 76 files, 2345 insertions, and 1246 deletions.
- Commit shape: 6 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 30 reviewable LOC across 3 production files and 76 total files.
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
- `tests/speckit-pro/layer4-scripts/test-l8-extractors.py`
- `tests/speckit-pro/layer4-scripts/test-l8-extractors.sh`
- `tests/speckit-pro/layer4-scripts/test-l8-judge.py`
- `tests/speckit-pro/layer4-scripts/test-l8-judge.sh`
- `tests/speckit-pro/layer4-scripts/test-layer8-runner.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer8-parity/01-post-impl-parity/README.md`
- `tests/speckit-pro/layer8-parity/01-post-impl-parity/env-fallback.json`
- `tests/speckit-pro/layer8-parity/01-post-impl-parity/env-fallback.sh`
- `tests/speckit-pro/layer8-parity/01-post-impl-parity/env-teams.json`
- `tests/speckit-pro/layer8-parity/01-post-impl-parity/env-teams.sh`
- `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/README.md`
- `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/env-fallback.json`
- `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/env-fallback.sh`
- `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/env-teams.json`
- `tests/speckit-pro/layer8-parity/02-prsg-011-migration-guidance/env-teams.sh`
- `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/README.md`
- `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/env-fallback.json`
- `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/env-fallback.sh`
- `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/env-teams.json`
- `tests/speckit-pro/layer8-parity/03-prsg-010-backstop-o5-routing/env-teams.sh`
- `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-fallback.json`
- `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-fallback.sh`
- `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-teams.json`
- `tests/speckit-pro/layer8-parity/04-prsg-014-stack-manager-guidance/env-teams.sh`
- `tests/speckit-pro/layer8-parity/README.md`
- `tests/speckit-pro/layer8-parity/lib/extractors.py`
- `tests/speckit-pro/layer8-parity/lib/extractors.sh`
- `tests/speckit-pro/layer8-parity/lib/judge.py`
- `tests/speckit-pro/layer8-parity/lib/judge.sh`
- `tests/speckit-pro/layer8-parity/run-parity-fixtures.py`
- `tests/speckit-pro/layer8-parity/run-parity-fixtures.sh`
- `tests/speckit-pro/parity/xplat-010/run-parity-fixtures-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-l8-extractors-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-l8-judge-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-l8-judge-bash-baseline.txt`
- `tests/speckit-pro/parity/xplat-010/test-layer8-runner-baseline.txt`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/suite-manifest.json`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/10-us7b` is the only immediate stack base.
- Traceability: `T073-T080` through marker `us10`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
