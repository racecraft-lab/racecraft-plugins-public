# Archival Report: DOC-011 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-011-github-pages-build-and-deploy-pipeline` | merged | cleanup applied | DOC-011 shipped through merged PR #243. The durable behavior now lives in the GitHub Pages deploy workflow, staging noindex/robots guard, CI/CD verification runbook, PR workflow lint coverage, release/runtime docs-reference alignment, shared spec-index guard hardening, generated payload copies, and process records; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/doc-011-archive-cleanup`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent (not created)
- Current target exclusion: none; DOC-011 was archived after PR #243 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #243 | `docs(DOC-011): add GitHub Pages deploy pipeline` | 2026-06-23T23:02:27Z | `538fb63323cb8b8562a246167eea9a46abcbc499` | `15a66732284ce5ff06b5821c8e3d44a63d20d0d3` | Deploy Docs GitHub Pages workflow, staging noindex/robots guard, CI/CD verification runbook, CLAUDE guidance, release workflow docs-reference runtime alignment, PR Checks workflow lint coverage, shared spec-index roadmap-MOC guard hardening, synced dist copies, focused structural/script tests, and final PR packet evidence |

- Source spec path:
  - `specs/doc-011-github-pages-build-and-deploy-pipeline`
- Source workflow:
  - `docs/ai/specs/.process/DOC-011-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/DOC-011-design-concept.md`
- Canonical shipped artifacts:
  - `.github/workflows/deploy-docs.yml`
  - `.github/workflows/pr-checks.yml`
  - `.github/workflows/release.yml`
  - `CLAUDE.md`
  - `docs-site/astro.config.mjs`
  - `docs-site/public/robots.txt`
  - `docs-site/scripts/validate-docs-quality.mjs`
  - `docs-site/src/content/docs/reference/tests.md`
  - `docs/ai/specs/cicd-release-pipeline-verification.md`
  - `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
  - `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
  - `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
  - `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
  - `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`
- CI evidence:
  - PR #243 checks passed: CodeQL, Analyze actions/javascript-typescript/python, detect, validate-pr-title, validate-workflows, validate-docs, test (speckit-pro), and validate-plugins.
  - PR Checks run: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/28051095171`
  - CodeQL runs: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/28051089830`, `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/28051089805`
  - Post-merge Deploy Docs run: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/28062949212`
- Post-merge deploy note:
  - The first post-merge `Deploy Docs` run failed in `actions/configure-pages` because repository Pages was not yet enabled/configured to build using GitHub Actions. This matches the documented manual operator prerequisite; enable Settings -> Pages -> Build and deployment -> Source: GitHub Actions before expecting publication.
- Screenshot retention: N/A; DOC-011 changed docs-site CI/CD and static staging guards, not visual UI. Playwright smoke evidence remains a short-retention CI artifact from docs validation when that workflow uploads it.
- Expiration risk: Low for committed artifacts; GitHub Actions logs and smoke artifacts may expire according to GitHub retention policy.

## Feature Summary

DOC-011 adds the first deploy-ready production-readiness slice for the
interactive documentation site. It introduces a standard GitHub Pages Actions
workflow that validates `docs-site/` before uploading `docs-site/dist`, publishes
through the `github-pages` environment with least-privilege Pages/OIDC
permissions, supports manual retry through `workflow_dispatch`, and uses a
single staging concurrency group for `main` deploys.

The feature keeps public launch explicitly deferred. It adds the staging
`noindex,nofollow` Starlight head guard, `docs-site/public/robots.txt` crawler
policy, docs-quality checks for both guards, and a CI/CD verification runbook
that separates one-time Pages setup, retry, rollback, deployment history, and
DOC-012 launch ownership. It also extends PR Checks with checksum-pinned
`actionlint` workflow lint coverage and aligns release PR docs-reference
generation with the docs-site Node 22 runtime.

During review, DOC-011 also hardened the shared SpecKit index generator so
roadmap-MOC generation fails safely when active specs are missing or partial.
That source fix, synced `dist/**` copies, and focused tests remain in committed
source/generator/test paths. The active DOC-011 spec folder can leave
`specs/**` because canonical behavior and operator guidance now live in durable
workflow, docs-site, runbook, generator, test, roadmap, memory, and archive
report paths.

## Recovery Commands

```text
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/SPEC-MOC.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/research.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/data-model.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/quickstart.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/contracts/deploy-docs-workflow.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/verify-tasks-report.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/requirements.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/integration.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/reliability.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/maintainability.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/checklists/security.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/.process/uat-runbook.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:docs/ai/specs/.process/DOC-011-workflow.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:docs/ai/specs/.process/DOC-011-design-concept.md
git checkout 538fb63323cb8b8562a246167eea9a46abcbc499 -- specs/doc-011-github-pages-build-and-deploy-pipeline
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-011 feature record |
| `.specify/memory/plan.md` | Appended DOC-011 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-011 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-011 archive cleanup notes and active docs deploy context |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-011 shipped and remaining production-readiness specs pending |
| `docs/traceability-interactive-documentation.md` | Clarified that DOC-011+ production-readiness extensions live in the technical roadmap outside the original DOC-001 through DOC-010 PRD traceability set |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-011 complete and archived; downstream specs now depend on the shipped staging deploy foundation |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Replaced active DOC-011 spec link with archive/report guidance; refreshed generated index |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Refreshed generated spec index output after active spec cleanup |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active DOC-011 state with completed DOC-011 archive state |
| `specs/doc-011-github-pages-build-and-deploy-pipeline` | Removed residual active spec evidence |

## Post-Cleanup Verification

- PASS: `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- PASS: `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`.
- PASS: stale active spec path scan found only intentional references -- archive report, project memory, recovery commands, preserved `.process/` workflow evidence, and generated/reference text explaining the post-merge archive.
- PASS: `git diff --check`
- PASS: `bash tests/speckit-pro/run-all.sh`

## Feature Status

DOC-011 is complete and archived. The interactive documentation roadmap now has
the staging GitHub Pages deploy foundation in place; DOC-012 remains the final
custom-domain, base-path, and indexing go-live gate, and DOC-013 through
DOC-021 remain pending production-readiness/content-excellence work.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. DOC-011 behavior changes remain in committed
workflow, docs-site, runbook, generator, test, and generated payload artifacts.
No plugin version, marketplace metadata, or release publication semantics are
changed by this archive cleanup.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-011-github-pages-build-and-deploy-pipeline`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- The merged DOC-011 active spec path contained specification, planning,
  checklist, contract, MOC, UAT runbook, reviewability, PR packet, and task
  evidence; this archive records recovery commands before removing that active
  source folder.
- The failed post-merge `Deploy Docs` run was classified as the documented
  manual GitHub Pages repository-setting prerequisite, not as a source cleanup
  blocker.

## Scoping

The cleanup removes only completed DOC-011 process/spec evidence from active
`specs/**`. The deploy workflow, staging indexing guards, CI/CD verification
runbook, workflow lint coverage, release runtime alignment, shared index
generator hardening, synced generated payloads, focused tests, workflow file,
design concept, roadmap, and archive report remain in durable repository paths.
