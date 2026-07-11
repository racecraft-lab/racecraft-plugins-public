<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/01-foundation/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 5, "deletions": 13747, "files": 35, "insertions": 150, "merge_commits": 0, "production_files": 0, "review_order": 2, "reviewable_loc": 0, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Remove orphaned Bash test scripts.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us1` maps this packet to T005-T007.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/00-process..xplat-010-review/01-foundation` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/00-process (da15f705d92973bf741e9728cf68e24e3a91807c)..xplat-010-review/01-foundation (1304d5a1fdbee4329d16385369a535bc2fc7a448)` contains 35 files, 150 insertions, 13747 deletions, and 0 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 2 of 18.
2. Compare `xplat-010-review/00-process` with `xplat-010-review/01-foundation` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/01-foundation` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 35 files, 150 insertions, and 13747 deletions.
- Commit shape: 5 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 0 reviewable LOC across 0 production files and 35 total files.
- Budget result: `within_budget`.
- Changed paths:
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-workflow.md`
- `tests/speckit-pro/layer4-scripts/test-aggregate-crl.sh`
- `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh`
- `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh`
- `tests/speckit-pro/layer4-scripts/test-confidence-gate.sh`
- `tests/speckit-pro/layer4-scripts/test-detect-commands.sh`
- `tests/speckit-pro/layer4-scripts/test-detect-presets.sh`
- `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
- `tests/speckit-pro/layer4-scripts/test-ensure-reviewability-preset.sh`
- `tests/speckit-pro/layer4-scripts/test-estimate-reviewable-loc.sh`
- `tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`
- `tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh`
- `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`
- `tests/speckit-pro/layer4-scripts/test-generate-uat-skeleton.sh`
- `tests/speckit-pro/layer4-scripts/test-install-codex-agents.sh`
- `tests/speckit-pro/layer4-scripts/test-install-curated-set.sh`
- `tests/speckit-pro/layer4-scripts/test-migrate-structure.sh`
- `tests/speckit-pro/layer4-scripts/test-moc-id-normalize.sh`
- `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
- `tests/speckit-pro/layer4-scripts/test-o5-topology.sh`
- `tests/speckit-pro/layer4-scripts/test-parse-consensus-categories.sh`
- `tests/speckit-pro/layer4-scripts/test-plan-layers.sh`
- `tests/speckit-pro/layer4-scripts/test-project-fixup.sh`
- `tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh`
- `tests/speckit-pro/layer4-scripts/test-resolve-confidence-mode.sh`
- `tests/speckit-pro/layer4-scripts/test-restack.sh`
- `tests/speckit-pro/layer4-scripts/test-reviewability-gate.sh`
- `tests/speckit-pro/layer4-scripts/test-validate-agent-install.sh`
- `tests/speckit-pro/layer4-scripts/test-validate-gate.sh`
- `tests/speckit-pro/layer4-scripts/test-validate-pr-packet.sh`
- `tests/speckit-pro/layer4-scripts/test-validate-pr-workflow-contract.sh`
- `tests/speckit-pro/layer4-scripts/test-validate-uat-runbook.sh`
- `tests/speckit-pro/parity/xplat-010/.gitkeep`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/00-process` is the only immediate stack base.
- Traceability: `T005-T007` through marker `us1`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
