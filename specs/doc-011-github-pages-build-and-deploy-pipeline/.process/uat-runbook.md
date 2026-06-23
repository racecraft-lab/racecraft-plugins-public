# UAT Runbook: doc-011-github-pages-build-and-deploy-pipeline

| Field | Value |
|-------|-------|
| Spec | doc-011-github-pages-build-and-deploy-pipeline |
| Branch | doc-011-github-pages-build-and-deploy-pipeline |
| PR | **PR:** [#243](https://github.com/racecraft-lab/racecraft-plugins-public/pull/243) |
| Generated from | 2026-06-23T01:51:13Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | _not available for this project_ |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | _not available for this project_ |
| INTEGRATION_TEST | _not available for this project_ |
| SINGLE_FILE_INTEGRATION | _not available for this project_ |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Deploy Docs After Main Merge (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Manually Retry A Deploy (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Preview Staging Without Public Discovery (Priority: P3)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-4"></a>
### User Story 4 - Follow Deploy Setup And Recovery Runbook (Priority: P4)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Deploy Docs After Main Merge (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Manually Retry A Deploy (Priority: P2)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Preview Staging Without Public Discovery (Priority: P3)](#us-3) | see the Per-Story Acceptance Tests block above |
| [User Story 4 - Follow Deploy Setup And Recovery Runbook (Priority: P4)](#us-4) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- A docs-impacting change outside `docs-site/src/content/docs/**` must still be eligible for automatic deployment if it can affect the rendered docs site.
- Multiple deploy runs for the same branch or environment must not publish overlapping artifacts unpredictably.
- A validation failure must leave the currently published staging site unchanged.
- A transient GitHub Pages or Actions failure on `main` must be recoverable through manual dispatch from `main` without changing source files.
- The staging site must remain directly previewable even while indexing and crawler discovery are blocked.
- The runbook must not imply that repository Pages settings are automated; maintainers perform one-time setup manually.

## Self-Review Findings

- Checked `.github/workflows/deploy-docs.yml` for the required push/manual triggers, explicit broad paths, ordered fixture exclusions, job-scoped least-privilege Pages permissions, main deploy concurrency, non-`main` no-op concurrency isolation, main-only manual retry guard, validate-before-upload ordering, same-run `docs-site/dist` artifact upload, and deploy-only `github-pages` job.
- Checked staging protection in source and generated output: `docs-site/public/robots.txt` has exactly the two required policy lines, and built HTML contains the `noindex, nofollow` meta guard.
- Checked runbook and CLAUDE guidance for manual Pages setup, retry/rollback distinction, deployment-history evidence, crawler-policy nuance, and DOC-012 launch boundary.
- No blocking self-review findings remain.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
