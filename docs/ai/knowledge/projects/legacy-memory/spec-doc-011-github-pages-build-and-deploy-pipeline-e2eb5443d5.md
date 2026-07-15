---
type: "speckit-legacy-memory-record"
title: "DOC-011 GitHub Pages Build-And-Deploy Pipeline"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-e2eb5443d5b7894c"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-011 GitHub Pages Build-And-Deploy Pipeline

### Summary

DOC-011 shipped the staging deployment foundation for the Astro/Starlight docs
site. It adds a standard GitHub Pages Actions workflow, validates the docs site
before artifact upload, preserves staging indexing protection with
`noindex,nofollow` and `robots.txt`, documents Pages setup/retry/rollback in the
CI/CD runbook, adds PR workflow lint coverage, aligns release docs-reference
generation with Node 22, and hardens the shared SpecKit roadmap-MOC index guard.

### User Stories

- **US1 - Deploy docs after main merge.** Maintainers can merge docs-impacting
  changes to `main` and receive a staging deploy after docs validation passes,
  once repository Pages is manually configured for GitHub Actions.
- **US2 - Manually retry a deploy.** Maintainers can dispatch the same deploy
  workflow from `main` for transient Actions or Pages failures.
- **US3 - Preview staging without public discovery.** Reviewers can open the
  staging Pages URL while the site still communicates crawler and indexing
  restrictions until DOC-012.
- **US4 - Follow deploy setup and recovery runbook.** Contributors and
  maintainers can find the deploy trigger, validation gate, one-time Pages
  setting, retry path, rollback path, and DOC-012 handoff.

### Functional Requirements

- Define `.github/workflows/deploy-docs.yml` using standard GitHub Pages
  actions, least-privilege `contents: read`, `pages: write`, and
  `id-token: write`, and no repository secrets or custom deploy tokens.
- Validate docs with `pnpm --dir docs-site validate` before uploading the
  generated `docs-site/dist` artifact.
- Support `push` to `main` through explicit docs-impacting path filters and
  `workflow_dispatch` retry from `main`.
- Keep build/upload and deploy as separate jobs, prevent overlapping staging
  deploys, and surface dependency, validation, upload, and deployment failures.
- Preserve staging non-indexing through the Starlight robots meta guard,
  `docs-site/public/robots.txt`, and docs-quality validation.
- Keep repository Pages settings manual, with DOC-012 owning custom domain,
  base-path migration, and removal of the indexing guard.

### Success Criteria

- Maintainers can identify one deploy workflow that validates and publishes the
  docs staging site after docs-impacting changes reach `main`.
- Maintainers can retry the deploy workflow without creating a source-only
  retry commit.
- Reviewers can preview a successful staging deploy while the site still carries
  non-indexing policy.
- The runbook documents setup, retry, rollback, deployment-history evidence, and
  the DOC-012 public-launch boundary.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #243 merged.
The first post-merge `Deploy Docs` run failed because repository Pages was not
yet enabled/configured for GitHub Actions, which is the documented manual
operator prerequisite. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md`.
