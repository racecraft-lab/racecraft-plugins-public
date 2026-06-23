<!-- speckit-pro-review-packet-source: specs/doc-011-github-pages-build-and-deploy-pipeline/.process/pr-packet/speckit-pr-packet.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Add a GitHub Pages deploy workflow for the docs site, plus the staging crawler guard and deployment verification runbook.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines reviewer-ready PR packet behavior.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added `.github/workflows/deploy-docs.yml` with pinned actions, job-scoped Pages/OIDC permissions, serialized main deploy concurrency, non-`main` no-op isolation, docs validation before artifact upload, and main-only manual retry support.
- Added PR workflow validation through pinned `actionlint` and expanded PR Checks docs/workflow detection so deploy workflow edits are validated before merge.
- Updated release workflow docs-reference sync runtime so release PRs regenerate checked-in docs references with the same Node/pnpm toolchain used elsewhere.
- Added `robots.txt` plus Starlight robots metadata to keep the pre-public staging docs non-indexable until DOC-012.
- Extended docs-quality validation and PR Checks docs detection so staging indexing guard changes are covered before deploy.
- Hardened the shared SpecKit roadmap-MOC index guard and synced/tested the generated Claude/Codex copies after PR review exposed a stale partial-home-note case.
- Added the CI/CD release pipeline verification guide and updated roadmap/runbook evidence for DOC-011.
<!-- speckit-pro-editable:what_changed:end -->

Source: schema contract defines editable field markers.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Docs can be built and deployed from `main` without exposing the staging site to public indexing, and maintainers get one source-backed recovery path for Pages setup, retry, rollback, and failure diagnosis.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review `.github/workflows/deploy-docs.yml` for the `main` push trigger, main-only manual retry guard, non-`main` no-op concurrency isolation, job-scoped Pages/OIDC permissions, serialized deploy concurrency, and validate-before-upload ordering.
2. Review `.github/workflows/pr-checks.yml` and `.github/workflows/release.yml` for workflow lint coverage, docs-validation detection, and release PR docs-reference regeneration.
3. Review `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`, matching `dist/` copies, and the new Layer 4 fixture/test for the partial roadmap-MOC fail-safe.
4. Review `docs-site/astro.config.mjs` and `docs-site/public/robots.txt` for the staging crawler guard.
5. Review `docs/ai/specs/cicd-release-pipeline-verification.md` and `CLAUDE.md` for the deploy setup, retry, rollback, and DOC-012 handoff guidance.

## How To UAT

Before merge, use the local docs validation evidence in the PR packet. After merge, confirm the `Deploy Docs` workflow publishes the `docs-site/dist` artifact to GitHub Pages and keep the staging noindex guard in place until the public-launch follow-up removes it.

## UAT Runbook

Use `specs/doc-011-github-pages-build-and-deploy-pipeline/.process/uat-runbook.md` for the post-merge deploy confirmation path. Live GitHub Pages verification is intentionally post-merge because DOC-011 does not automate repository Pages settings.

## Verification

- `actionlint .github/workflows/*.yml` passed.
- `pnpm --dir docs-site validate` passed.
- `bash tests/speckit-pro/run-all.sh` passed `3478/3478`.
- `validate-pr-packet.sh` and `validate-pr-workflow-contract.sh` passed.
- GitHub PR Checks and CodeQL passed on PR #243.

Source: generated PR packet.

## Scope

- Source feature: GitHub Pages docs deployment workflow and staging crawler guard.
- Scope: this PR adds the deploy workflow, workflow-lint PR check, docs-site noindex/robots guard, release PR docs-reference runtime alignment, deploy verification runbook, CLAUDE.md pointer, shared spec-index guard hardening with dist/test coverage, and SpecKit evidence for DOC-011.
- Size: the packet records 54 changed files. The reviewability gate's production-only metrics are 36 LOC across 2 production files; the final gate is size-blocked by total-file count and proceeds through one atomic PR marker.
- Traceability: feature spec, rendered body, final reviewability gate, validation output, and changed-file scope are recorded in the packet metadata.
- Non-goals: automating repository Pages settings, custom domain launch, public indexing, and removing staging noindex controls.

## Known Gaps

Live GitHub Pages deployment can only be confirmed after merge and repository Pages settings are available.
