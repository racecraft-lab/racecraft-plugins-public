<!-- speckit-pro-review-packet-source: specs/xplat-010-repository-bash-confinement/.process/pr-packets/17-polish/packet.json -->
<!-- xplat010-finalization-metrics:{"commit_count": 5, "deletions": 701, "files": 57, "insertions": 3335, "merge_commits": 0, "production_files": 4, "review_order": 18, "reviewable_loc": 640, "total_slices": 18} -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Finalize integrated verification evidence.
<!-- speckit-pro-editable:summary:end -->

Source: canonical marker `polish` maps this packet to T131-T136.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Materializes the exact `xplat-010-review/16-release-composition..xplat-010-review/17-polish` stack slice.
- Records the adjacent Git diff and reviewer packet from current branch objects.
<!-- speckit-pro-editable:what_changed:end -->

Source: adjacent diff `xplat-010-review/16-release-composition (b5ab3cac69013207a47f431f490231a9b2d5441e)..xplat-010-review/17-polish (a7b2d27b12fdc5051dfa4829c94f92752e2f5146)` contains 57 files, 3335 insertions, 701 deletions, and 640 reviewable LOC.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
This keeps the dependent PR independently reviewable while preserving a gapless linear stack.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review order: 18 of 18.
2. Compare `xplat-010-review/16-release-composition` with `xplat-010-review/17-polish` and inspect the changed-path inventory below.
3. Confirm the packet target, branch OIDs, and local verification record use this same adjacent boundary.

## How To UAT

Use the committed feature UAT runbook on `xplat-010-review/17-polish` and record command, exit-code, and observable-result evidence.

## UAT Runbook

Source: `specs/xplat-010-repository-bash-confinement/.process/uat-runbook.md` is the acceptance procedure. This packet does not promote local evidence to hosted, merged, or published evidence.

## Verification

- Diff metrics: 57 files, 3335 insertions, and 701 deletions.
- Commit shape: 5 commits and 0 merge commits.
- Exact adjacent-diff packet coverage and remote OID checks are enforced by `scripts/xplat010-finalize-stack.py verify`.

## Scope

- Exact scope: 640 reviewable LOC across 4 production files and 57 total files.
- Budget result: `warning`.
- Changed paths:
- `.github/copilot-instructions.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`
- `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md`
- `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`
- `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md`
- `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md`
- `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/prd-interactive-documentation.md`
- `docs/prd-pr-size-governance.md`
- `docs/prd-tool-agnostic-capability-discovery.md`
- `docs/roadmap-interactive-documentation.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`
- `speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/SKILL.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-reviewability-marker-guidance.py`
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- Non-goals: No later slice, merge, hosted-check result, or release publication is claimed.
- Dependencies: `xplat-010-review/16-release-composition` is the only immediate stack base.
- Traceability: `T131-T136` through marker `polish`.
- Rollback: Revert this adjacent slice without restoring a retired Bash runtime path.
- Publication tail: This packet remains frozen to its implementation-adjacent diff if later explicitly contracted metadata-only commits advance the live top branch.

## Known Gaps

Hosted and post-merge evidence remains pending unless separately recorded by the live PR checks.

## Release note

Not required for this Conventional Commit type.
