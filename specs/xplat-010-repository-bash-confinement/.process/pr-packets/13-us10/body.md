<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/13-us10/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 5, "deletions": 102119, "files": 1401, "insertions": 110937, "merge_commits": 0, "production_files": 14, "review_order": 14, "reviewable_loc": 1885, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Enforce repository Bash confinement.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `us12` maps this packet to T088-T099.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/12-us9..xplat-010-review/13-us10` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/12-us9 (3348aa4fbb80373b39fedbd18003c63f5c33862d)..xplat-010-review/13-us10 (93aaddd09d04a89b60bdc0085073a732b95e705c)` contains 1401 files, 110937 insertions, 102119 deletions, and 1885 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 14 of 18.
2. Compare `xplat-010-review/12-us9` with `xplat-010-review/13-us10` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/13-us10` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 1401 files, 110937 insertions, and 102119 deletions.
- Commit shape: 5 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 1885 reviewable LOC across 14 production files and 1401 total files.
- Budget result: `exception`.
- Changed paths:
- `.github/copilot-instructions.md`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `.specify/memory/archive-reports/2026-06-09-prsg-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-10-prsg-008-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-11-prsg-009-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`
- `.specify/memory/changelog.md`
- `.specify/memory/constitution.md`
- `.specify/memory/plan.md`
- `.specify/memory/spec.md`
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `dist/claude/speckit-pro/README.md`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/registry.py`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/release.py`
- `dist/claude/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/install.py`
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/claude/speckit-pro/speckit_pro_runner/runtime.py`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `dist/codex/speckit-pro/README.md`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/payloads.py`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/registry.py`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/release.py`
- `dist/codex/speckit-pro/speckit_pro_runner/gates/suite.py`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/install.py`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/codex/speckit-pro/speckit_pro_runner/runtime.py`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- `docs/ai/specs/.process/DOC-010-workflow.md`
- `docs/ai/specs/.process/PRSG-002-workflow.md`
- `docs/ai/specs/.process/PRSG-003-workflow.md`
- `docs/ai/specs/.process/PRSG-006-design-concept.md`
- `docs/ai/specs/.process/PRSG-006-workflow.md`
- `docs/ai/specs/.process/PRSG-007-design-concept.md`
- `docs/ai/specs/.process/PRSG-007-workflow.md`
- `docs/ai/specs/.process/PRSG-008-workflow.md`
- `docs/ai/specs/.process/PRSG-009-workflow.md`
- `docs/ai/specs/.process/PRSG-011-workflow.md`
- `docs/ai/specs/.process/PRSG-012-workflow.md`
- `docs/ai/specs/.process/PRSG-013-final-marker-split-result.json`
- `docs/ai/specs/.process/PRSG-013-final-reviewability-state.json`
- `docs/ai/specs/.process/PRSG-013-marker-emission-dry-run.json`
- `docs/ai/specs/.process/PRSG-013-pr-marker-plan.json`
- `docs/ai/specs/.process/PRSG-013-workflow.md`
- `docs/ai/specs/.process/PRSG-014-workflow.md`
- `docs/ai/specs/.process/TACD-002-workflow.md`
- `docs/ai/specs/.process/XPLAT-004-workflow.md`
- `docs/ai/specs/.process/XPLAT-005-workflow.md`
- `docs/ai/specs/.process/XPLAT-006-workflow.md`
- `docs/ai/specs/.process/XPLAT-007-workflow.md`
- `docs/ai/specs/.process/XPLAT-008-release-readiness.md`
- `docs/ai/specs/.process/XPLAT-008-workflow.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-pr-body.md`
- `docs/ai/specs/.process/XPLAT-009-pr-packet.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-009-source-inventory.md`
- `docs/ai/specs/.process/XPLAT-009-workflow.md`
- `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- `docs/ai/specs/.process/XPLAT-010-count-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md`
- `docs/ai/specs/.process/XPLAT-010-design-concept.md`
- `docs/ai/specs/.process/XPLAT-010-workflow.md`
- `docs/ai/specs/.process/autopilot-state.json`
- `docs/ai/specs/PRSG-001-design-concept.md`
- `docs/ai/specs/PRSG-001-workflow.md`
- `docs/ai/specs/SPEC-001-workflow.md`
- `docs/ai/specs/SPEC-002-workflow.md`
- `docs/ai/specs/SPEC-003-workflow.md`
- `docs/ai/specs/SPEC-004-workflow.md`
- `docs/ai/specs/SPEC-006a-design-concept.md`
- `docs/ai/specs/SPEC-006a-workflow.md`
- `docs/ai/specs/cicd-release-pipeline-technical-roadmap.md`
- `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
- `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`
- `docs/ai/specs/reviewer-experience-technical-roadmap.md`
- `docs/prd-interactive-documentation.md`
- `scripts/refresh-local-plugin.py`
- `scripts/refresh-release-artifacts.py`
- `scripts/sync_release_pr.py`
- `speckit-pro/README.md`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/gates/suite.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `specs/xplat-010-repository-bash-confinement/contracts/count-parity-baseline.contract.md`
- `specs/xplat-010-repository-bash-confinement/contracts/estimate-spec-size.schema.json`
- `specs/xplat-010-repository-bash-confinement/data-model.md`
- `specs/xplat-010-repository-bash-confinement/plan.md`
- `specs/xplat-010-repository-bash-confinement/quickstart.md`
- `specs/xplat-010-repository-bash-confinement/research.md`
- `specs/xplat-010-repository-bash-confinement/spec.md`
- `specs/xplat-010-repository-bash-confinement/tasks.md`
- `tests/speckit-pro/check-toolchain.py`
- `tests/speckit-pro/layer1-structural/fixtures/spec-index/README.md`
- `tests/speckit-pro/layer1-structural/validate-agents.py`
- `tests/speckit-pro/layer1-structural/validate-capability-pointer.py`
- `tests/speckit-pro/layer1-structural/validate-capability-resolution.py`
- `tests/speckit-pro/layer1-structural/validate-codex-agents.py`
- `tests/speckit-pro/layer1-structural/validate-codex-hooks.py`
- `tests/speckit-pro/layer1-structural/validate-codex-marketplace.py`
- `tests/speckit-pro/layer1-structural/validate-codex-parity.py`
- `tests/speckit-pro/layer1-structural/validate-codex-plugin.py`
- `tests/speckit-pro/layer1-structural/validate-codex-skills.py`
- `tests/speckit-pro/layer1-structural/validate-curated-set.py`
- `tests/speckit-pro/layer1-structural/validate-hooks.py`
- `tests/speckit-pro/layer1-structural/validate-moc-orphan.py`
- `tests/speckit-pro/layer1-structural/validate-moc-stale-index.py`
- `tests/speckit-pro/layer1-structural/validate-payload-completeness.py`
- `tests/speckit-pro/layer1-structural/validate-payload-conformance.py`
- `tests/speckit-pro/layer1-structural/validate-plugin-payload.py`
- `tests/speckit-pro/layer1-structural/validate-plugin.py`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py`
- `tests/speckit-pro/layer1-structural/validate-process-gitattributes.py`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.py`
- `tests/speckit-pro/layer1-structural/validate-scripts.py`
- `tests/speckit-pro/layer1-structural/validate-skill-capability-pointers.py`
- `tests/speckit-pro/layer1-structural/validate-skills.py`
- `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.py`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/additive-multi-seam/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/concurrency/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-conflict/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-consumer-locality/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-consumer-out-of-tree/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-guarded-cutover/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-release-held/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/context-weak-evidence/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/dogfood-prsg-007/contracts/routing-decision.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/dogfood-prsg-007/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/dogfood-prsg-007/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/dogfood-prsg-007/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-destructive-migration/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-mutual-exclusion/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-out-of-tree-contract/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-rename/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/hard-atomic-version-pin/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/modify-heavy/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/out-of-scope-empty/.gitkeep`
- `tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/single-additive-seam/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/all-absent.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/all-absent.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/at-ceiling.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/at-ceiling.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/bad-input.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/bad-input.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/mixed-valid-bad.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/mixed-valid-bad.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/modify-discount.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/modify-discount.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/multi-slice.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/multi-slice.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/over-ceiling.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/over-ceiling.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/spike-precedence.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/spike-precedence.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/spike.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/spike.json`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/typical-under.args`
- `tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/typical-under.json`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/block-no-exception/gate-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/gate-error/gate-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/generated-boilerplate/gate-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/generated-boilerplate/template.md`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/valid-refactor-exception/exception.md`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/valid-refactor-exception/gate-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/final-reviewability-backstop/warn/gate-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/hazard-route.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/reviewability-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/canonical/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/current-source-fingerprint.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/final-marker-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/fingerprint-mismatch-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/hazard-route.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/reviewability-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-collapse/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-single-atomic-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/hazard-unreleasable-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/malformed-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/malformed-pr-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/malformed-reviewability/reviewability-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/mismatched-marker-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/navigable-releasable-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/hazard-route.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/reviewability-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/no-safe-boundary/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/order-mismatch-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/placeholder-pr-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/prsg-012-final-marker-split-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/prsg-012-pr-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/hazard-route.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/reviewability-result.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/safe-subdivision/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/stale-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/stale-pr-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/stale-state/state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/valid-autopilot-state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/valid-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/valid-pr-marker-plan.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/emission-state/duplicate-slice-keys.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/emission-state/empty-autopilot-state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/emission-state/pending-valid.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/input-error-status.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/invalid-status.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/malformed.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/valid-single-slice.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/valid-three-slice.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/prs-manifests/schema-v1-root/specs/prsg-920-prs-v1/.process/prs.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/prs-manifests/schema-v1-root/specs/prsg-920-prs-v1/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/prs-manifests/schema-v2-root/specs/prsg-921-prs-v2/.process/prs.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/prs-manifests/schema-v2-root/specs/prsg-921-prs-v2/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/malformed-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-prs-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-stack-state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/scoped-verification/failed.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/scoped-verification/no-scoped-tests.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/scoped-verification/passed.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/slice-packets/invalid-missing-slice-id.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/slice-packets/malformed.json`
- `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/slice-packets/valid-foundation.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/bash-reference-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/autopilot-phase-coverage-report.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/doctor-preflight-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/helper-promotion-record.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/mutation-helper-request.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/mutation-helper-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/fixture-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/install-inventory-fixtures.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/promotion-records.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/doctor-preflight.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/doctor-repair.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/generate-pr-body.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/multi-pr-emission.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/mutation-foundation.json`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/requests/mutation-registry-dispatch.json`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/specs/prsg-501-o5-parent/o5-parent-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/specs/prsg-501a-alpha/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/invalid-topology/specs/prsg-501c-gamma/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502-o5-parent/o5-parent-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502a-blocked/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502b-failed/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502c-progress/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502d-pending/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502e-complete/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502f-archived/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/mixed-child-states/specs/prsg-502g-missing-state/README.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/specs/prsg-500-o5-parent/o5-parent-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/specs/prsg-500a-alpha/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/specs/prsg-500b-beta/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/o5-topology/valid-parent/specs/prsg-500c-gamma/SPEC-MOC.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/checkbox-state/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/dependency-cycle/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/empty-increment/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-dependency/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-reference/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/malformed-task/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-headings/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-references/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/path-normalization/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/invalid-protected-edit.md`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single-edited.md`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-single.md`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/bodies/valid-split.md`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-malformed-json.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-evidence.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-missing-packet.args`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-no-feature-dir.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-protected-edit.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-schema-with-feature-dir.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-title-token.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/split-partial-failure-state.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-single.json`
- `tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json`
- `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract/.process/uat-runbook.md`
- `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract/contracts/pr-packet.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract/quickstart.md`
- `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/changed-files-xplat-005.txt`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/normalization-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/atomicity-route.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/check-prerequisites.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/confidence-gate.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/count-markers.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/detect-commands.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/detect-presets.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/estimate-reviewable-loc.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/estimate-spec-size.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/generate-spec-index-check.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/helper-registry-dispatch.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/o5-topology.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/plan-layers-feature-dir.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/resolve-confidence-mode.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/reviewability-gate.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/validate-gate.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/validate-pr-packet-read-only.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/validate-pr-workflow-contract.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/smoke-runtime-info-request.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/synthetic-paths.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/checklists/error-handling.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/checklists/integration.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/checklists/reliability.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/checklists/requirements.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/checklists/security.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/plan.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/spec.md`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/tasks.md`
- `tests/speckit-pro/layer4-scripts/fixtures/spec-full-snapshot.md`
- `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/changed-files-xplat-004.txt`
- `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json`
- `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/platform-runbook-fixtures.md`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/README.md`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/cases/detection-matrix.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/duplicate-retry/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/fallback/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/partial-mutation/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/emission/supported/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/expected/decision-supported.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/missing/gh`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/supported/gh`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/fake-gh/unsupported/gh`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/packets/valid-prsg-014/README.md`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/packets/valid-prsg-014/packet.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/packets/valid-prsg-014/pr-body.md`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/blocked-resume/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/fallback/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/partial-mutation/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/restack/supported/scenario.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/schema/stack-manager-decision-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/stack-manager/topology/prsg-014-prs.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/active-path-guard-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/install-verification-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/migrated-gate-request.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/migrated-gate-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/payload-evidence.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/promotion-record.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/release-readiness-result.schema.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/active-path-guard.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/classify-shell-finding.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness-live-github.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-ai-evals.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-integration-suite.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-layer.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-parity-suite.json`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight-docs.json`
- Inventory note: showing 405 of 1401 changed paths; the complete adjacent-diff inventory is in the packet JSON.
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/12-us9` is the only immediate stack base.
- Traceability: `T088-T099` through marker `us12`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

```release-note
Enforce repository Bash confinement.
```
