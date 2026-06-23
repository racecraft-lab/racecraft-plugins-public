# CI/CD Release Pipeline Verification

Use this runbook when a change touches `.github/workflows/**`, release automation, branch-protection guidance, or the docs-site deploy path.

## Baseline Checks

1. Confirm PR titles still use Conventional Commits.
2. Confirm `.github/workflows/pr-checks.yml` still exposes the expected branch-protection checks: `validate-pr-title`, `validate-workflows`, `validate-docs`, and `validate-plugins`.
3. Confirm `.github/workflows/release.yml` still lets release-please open or update release PRs, sync generated plugin payloads, regenerate docs reference pages, and dispatch PR Checks for release PR branches.
4. If any workflow job is renamed, compare branch protection against the workflow names before merging:

   ```bash
   gh api /repos/racecraft-lab/racecraft-plugins-public/branches/main/protection \
     --jq '[.required_status_checks.contexts[]]'
   ```

## Deploy Docs Workflow

`.github/workflows/deploy-docs.yml` publishes the Astro/Starlight docs site to the staging GitHub Pages environment after docs validation succeeds.

- Automatic trigger: `push` to `main` for docs-site, generated-reference, marketplace, release, workflow, and plugin-source paths that can affect published docs.
- Manual retry trigger: `workflow_dispatch` from `main` only; manually selected non-`main` refs do not deploy to the shared staging environment.
- Validation gate: `pnpm --dir docs-site validate`.
- Artifact: `docs-site/dist`, created after the workflow removes any stale local `docs-site/dist`.
- Environment: `github-pages`.
- Concurrency: `main` deploy runs use fixed group `deploy-docs-github-pages` with `cancel-in-progress: true`; skipped non-`main` manual dispatch runs use a unique no-op group and must not cancel a `main` deploy.
- Credentials: build job has `contents: read`; deploy job has standard GitHub Pages `pages: write` and OIDC context only. No secrets, deploy keys, personal access tokens, GitHub App tokens, or custom deploy token inputs are used.

## One-Time Pages Setup

A repository maintainer must configure Pages manually before expecting the workflow to publish.

1. Open the repository in GitHub.
2. Go to `Settings -> Pages -> Build and deployment`.
3. Set `Source` to `GitHub Actions`.
4. Do not select branch-based publishing.
5. Verify that successful deploys are recorded through the `github-pages` environment.

DOC-011 does not automate Pages settings through the GitHub API or CLI because the setting is repository administration state.

## Local Validation

Run the same docs gate used by the deploy workflow:

```bash
corepack enable
corepack prepare pnpm@10.25.0 --activate
pnpm --dir docs-site install --frozen-lockfile
pnpm --dir docs-site exec playwright install --with-deps chromium
rm -rf docs-site/dist
pnpm --dir docs-site validate
```

Expected result: validation succeeds and `docs-site/dist` exists with static output.

## Merge-Time Verification

After a DOC-011 deploy-related PR merges to `main`, open the `Deploy Docs` workflow run and record:

- Source ref and commit SHA.
- Dependency install result.
- Docs validation result.
- Pages artifact upload result.
- Pages deploy result.
- Deployed URL from the deploy job output or GitHub deployment history.

If validation or upload fails, the currently published staging site should remain unchanged because deploy depends on the validated artifact job.

## Manual Retry

Use `workflow_dispatch` only for transient dependency, Actions, artifact upload, or Pages service failures when the source commit is still correct.

1. Open `Actions -> Deploy Docs`.
2. Select `Run workflow`.
3. Select `main` as the branch.
4. Confirm the new run repeats dependency install, docs validation, artifact upload, and deploy.

Do not use manual retry to bypass a validation failure or deploy an unmerged branch. Fix the source problem through a PR first, then retry from `main` if the merged source is still correct.

## Rollback

Pages artifacts are run-scoped deployment inputs, not durable rollback assets.

If bad source content deploys:

1. Revert or fix forward through a normal PR.
2. Let PR Checks validate the correction.
3. Merge to `main`.
4. Confirm a fresh `Deploy Docs` run validates and deploys the corrected `docs-site/dist`.

## Failure Symptoms

- Dependency install failure: `Install docs-site dependencies` fails before validation.
- Browser install failure: `Install Playwright Chromium` fails before validation.
- Validation failure: `Validate docs-site` fails and no artifact should be uploaded.
- Empty artifact failure: `Validate docs-site` reports `docs-site/dist` missing or empty after validation.
- Upload failure: `Upload Pages artifact` fails and the deploy job should not run.
- Deploy failure: `Deploy Pages artifact` fails; inspect workflow logs and GitHub deployment history for the source SHA, environment, and status.

## Staging Indexing Guard

DOC-011 keeps the staging GitHub Pages project site previewable by known URL but not intended for public discovery.

- `docs-site/astro.config.mjs` adds the page-level `noindex, nofollow` robots meta tag. This is the primary indexing guard because crawlers that can see the page can see the directive.
- `docs-site/public/robots.txt` contains `User-agent: *` and `Disallow: /`. On a GitHub Pages project site, this is policy/signaling because crawlers look for `robots.txt` at the host root.
- `robots.txt` blocks crawling; `noindex` blocks indexing when crawlers can see the page.

DOC-012 owns the launch boundary: custom domain, base-path migration if needed, and removal of the `noindex`/`robots` staging protection.
