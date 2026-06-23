# Quickstart: GitHub Pages Build-And-Deploy Pipeline

## Prerequisites

- Node >=22.12.
- Corepack available.
- GitHub repository Pages setting manually configured by a maintainer: `Settings -> Pages -> Build and deployment -> Source = GitHub Actions`.
- Implementation branch contains DOC-011 workflow, staging guard, runbook, and CLAUDE.md updates.

## Local Validation

1. Activate the docs-site package manager.

   ```bash
   corepack enable
   corepack prepare pnpm@10.25.0 --activate
   ```

2. Install docs-site dependencies.

   ```bash
   pnpm --dir docs-site install --frozen-lockfile
   ```

3. Install the browser required by the smoke test.

   ```bash
   pnpm --dir docs-site exec playwright install --with-deps chromium
   ```

4. Run the deploy gate locally.

   ```bash
   rm -rf docs-site/dist
   pnpm --dir docs-site validate
   ```

Expected result: validation succeeds and `docs-site/dist` exists.

## Workflow Contract Checks

1. Confirm `.github/workflows/deploy-docs.yml` uses `workflow_dispatch` and `push` to `main` with explicit `paths`.
2. Confirm the workflow declares only `contents: read`, `pages: write`, and `id-token: write`.
3. Confirm the workflow does not reference `${{ secrets.* }}`, deploy keys, personal access tokens, GitHub App tokens, custom `token:` inputs, or broad/default write permissions.
4. Confirm the workflow has separate build/upload and deploy jobs, with deploy depending on the validated artifact job.
5. Confirm the artifact upload path is `docs-site/dist`.
6. Confirm `docs-site/dist` is removed before validation and uploaded only after `pnpm --dir docs-site validate` succeeds.
7. Confirm deploy uses the `github-pages` environment.
8. Confirm `main` deploys use the fixed staging group `deploy-docs-github-pages` with `cancel-in-progress: true`, and skipped non-`main` manual dispatch runs use a no-op group that cannot cancel a `main` deploy.
9. Confirm the deploy job does not checkout, rebuild, or upload an artifact.

## Staging Indexing Checks

1. Confirm `docs-site/public/robots.txt` contains exactly:

   ```text
   User-agent: *
   Disallow: /
   ```

2. Confirm `docs-site/astro.config.mjs` includes one global Starlight `head` robots meta entry with `noindex, nofollow`.
3. Confirm the runbook explains that `robots.txt` blocks crawling, while `noindex` blocks indexing when crawlers can see the page.
4. Confirm the runbook names DOC-012 as the owner for removing staging indexing protection.

## GitHub Pages Setup And Retry

1. In repository settings, configure Pages source as GitHub Actions.
2. Merge a DOC-011 implementation PR to `main`.
3. Observe the `Deploy Docs` workflow.
4. For any run, record the source ref/SHA, validation result, artifact upload result, deploy result, and deployed URL from the workflow run summary/logs and GitHub deployment history.
5. If dependency installation, artifact upload, or Pages deployment fails for a transient external reason while source remains correct, manually dispatch the workflow from GitHub Actions so a new artifact is built and validated before deployment.
6. If validation fails, fix the source problem first; do not use a deploy-only rerun as a bypass.
7. If a bad source change deployed, revert or fix forward through a normal PR and let a fresh successful deploy workflow publish the corrected staging site.

## DOC-012 Handoff

DOC-011 must leave the current GitHub Pages project-site URL, `base`, and staging indexing protection in place. DOC-012 owns the custom domain, base-path migration, and removal of `noindex`/`robots` staging protection.
