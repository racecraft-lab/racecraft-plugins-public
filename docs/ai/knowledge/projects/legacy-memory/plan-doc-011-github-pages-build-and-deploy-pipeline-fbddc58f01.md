---
type: "speckit-legacy-memory-record"
title: "DOC-011 GitHub Pages Build-And-Deploy Pipeline"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-fbddc58f018aa8d2"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-011 GitHub Pages Build-And-Deploy Pipeline

### Scope

Ship the staging GitHub Pages deployment foundation for the existing
Astro/Starlight docs site without expanding into public launch. DOC-011 owns the
deploy workflow, validation-before-upload gate, staging noindex/robots guard,
operator runbook, PR workflow lint coverage, release docs-reference runtime
alignment, and the shared roadmap-MOC index guard hardening discovered during
review.

### Architecture / Approach

- Use standard GitHub Pages Actions in `.github/workflows/deploy-docs.yml`
  rather than a custom deploy script or API-based repository setting mutation.
- Run the existing docs validation path, `pnpm --dir docs-site validate`, before
  uploading `docs-site/dist` as the Pages artifact.
- Keep Pages setup manual in repository settings and document it in
  `docs/ai/specs/cicd-release-pipeline-verification.md`.
- Preserve the current GitHub Pages project-site URL/base assumptions and keep
  `noindex,nofollow` plus `robots.txt` staging protection until DOC-012.
- Add checksum-pinned `actionlint` coverage in PR Checks and keep deploy-related
  workflow changes inside the plugin structural validation trigger surface.
- Keep the shared `generate-spec-index.sh` guard fix in source, synced `dist/**`
  payload copies, and focused tests.

### Test Strategy

- Confirm PR #243 merged to `main`.
- Validate JSON state after replacing the active DOC-011 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run `git diff --check` and `bash tests/speckit-pro/run-all.sh`.
- Record the post-merge `Deploy Docs` failure as an operational Pages setup
  prerequisite until repository Settings -> Pages is configured for GitHub
  Actions.

### Cleanup Notes

`specs/doc-011-github-pages-build-and-deploy-pipeline` was removed from active
`specs/**` cleanup after the deploy workflow, staging indexing guards, CI/CD
runbook, workflow lint gate, release runtime alignment, shared index generator
hardening, synced payloads, tests, and PR packet evidence landed through PR
#243. Recovery commands and provenance are recorded in the DOC-011 archive
report.
