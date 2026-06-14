# Archival Report: DOC-002 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-002-unified-landing-page-and-ia-shell` | merged | cleanup applied | DOC-002 shipped through merged PRs #173-#176, PR #177 repaired the autopilot continuation bug found during final emission, provenance and recovery commands are recorded, and no production or test script depends on the live spec folder |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly.
- Cleanup branch: `codex/doc-002-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before DOC-002 archival edits: clean after committing the independent release workflow fix.
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-002 was archived after all implementation PRs merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit |
|----|-------|-----------|--------------|
| #173 | `feat(speckit-pro): Add docs site foundation` | 2026-06-14T16:24:59Z | `0bb5e6b5f7589a7872819a2fe3c0ddb583e63565` |
| #174 | `feat(speckit-pro): Add landing page platform choice` | 2026-06-14T17:35:09Z | `ce59667582a4bd656eface86a850293b98d50ad5` |
| #175 | `feat(speckit-pro): Add IA route shell navigation` | 2026-06-14T17:56:59Z | `e52035516f3434b82d728e32d3834f24400140cd` |
| #176 | `feat(speckit-pro): Add docs validation and review evidence` | 2026-06-14T19:37:43Z | `73ad7c97a44b036be9247d8e5910587ce61d9ae6` |
| #177 | `fix(autopilot): require reslice continuation` | 2026-06-14T19:38:25Z | `4fc5f81363e5b99e71d298390785d4d4c70d86ae` |

- Source spec path: `specs/doc-002-unified-landing-page-and-ia-shell`
- Tree reference after PR #177: `ecb354cbc8cefba8ed486a87a3f0226d608162cc`
- Artifact manifest: `specs/doc-002-unified-landing-page-and-ia-shell/SPEC-MOC.md`
- Canonical deliverable: `docs-site/`
- Archive report: `.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`
- Screenshot retention: N/A; browser UAT evidence is textual.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-002 created the Astro/Starlight documentation site shell for Racecraft Public
Plugins. It added the `docs-site/` package, Starlight/Astro config, pnpm
lockfile, landing page, Diataxis sidebar groups, all 11 top-level route shells,
source-vs-generated-payload explanation, Pages-ready base path handling, and
internal-link validation through `starlight-links-validator`.

The feature deliberately stayed at shell/content-skeleton depth. DOC-003 and
DOC-004 own full platform-specific install content, DOC-006 owns interactive
selectors, and DOC-010 owns broader search, accessibility, responsive,
deep-link, deployment, and docs CI hardening.

## Task Completion

- `tasks.md`: 42 / 43 implementation tasks checked complete.
- Historical exception: T041 remained unchecked because the original one-PR PR
  packet path was blocked by the final reviewability backstop. The work was
  instead emitted, reviewed, remediated, and merged through PRs #173-#176, and
  PR #177 fixed the autopilot continuation bug so this stop condition does not
  recur.
- Checklist closure: accessibility, error-handling, reliability, and UX
  checklists are complete.

## Recovery Commands

```text
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/spec.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/plan.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/tasks.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/research.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/data-model.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/quickstart.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/SPEC-MOC.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/contracts/route-shell-manifest.json
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/checklists/accessibility.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/checklists/error-handling.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/checklists/reliability.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/checklists/ux.md
git checkout 4fc5f81363e5b99e71d298390785d4d4c70d86ae -- specs/doc-002-unified-landing-page-and-ia-shell
```

## Pre-Cleanup Verification

- `gh pr view 173-177` confirmed the DOC-002 stack and the autopilot repair PR
  are merged to `main`.
- `gh release list` confirmed the latest completed GitHub release before the
  current release PR is `speckit-pro-v2.13.0`.
- `gh pr view 178` confirmed release-please opened PR #178 for
  `speckit-pro 2.13.1`.
- `gh pr checks 178` initially showed `test (speckit-pro)` and
  `validate-plugins` failing because generated payload files were stale.

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  passed with `spec-index: index current`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `cd docs-site && pnpm check` passed with 0 errors, 0 warnings, and 0 hints.
- `cd docs-site && pnpm build` passed; 12 pages built and all internal links
  were valid.
- `cd docs-site && pnpm validate:links` passed.
- `cd docs-site && pnpm validate` passed.
- `bash tests/speckit-pro/run-all.sh` passed `2925/2925`.
  - Layer 1 structural: `551/551`.
  - Layer 1 Codex structural: `430/430`.
  - Layer 4 script unit: `1754/1754`.
  - Layer 5 tool scoping: `190/190`.
- `git diff --check` passed.
- Stale active DOC-002 link scan passed for retained docs and memory files.
- PR #178 is mergeable with green `detect`, `validate-pr-title`,
  `test (speckit-pro)`, `validate-plugins`, and CodeQL checks at head
  `bd47e008b73b39bc0270b38995c59fa32bbb70ae`.

## Concurrent Release PR Repair

This branch also includes a separate durable release workflow fix:

- PR #178 failed because release-please bumped source plugin versions and
  changelogs, but the Release workflow queried just-created pending labels and
  found zero PRs before synchronizing generated `dist/` payloads.
- `.github/workflows/release.yml` now consumes `steps.release.outputs.prs`
  directly and fails loudly if `prs_created=true` has no PR metadata.
- `tests/speckit-pro/layer1-structural/validate-release-workflow.sh` now guards
  against reintroducing the label-query race.
- The current PR #178 branch received generated payload commit `bd47e00`.
  PR Checks and CodeQL are green on the updated release branch.

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-002 feature record |
| `.specify/memory/plan.md` | Appended DOC-002 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-002 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-002 archive cleanup note |
| `docs/traceability-interactive-documentation.md` | Marked DOC-002 completed and DOC-003/DOC-004 next |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-002 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-002 archived and DOC-003/DOC-004 ready |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Removed generated active-spec link after cleanup |
| `docs/ai/specs/.process/DOC-002-workflow.md` | Recorded completed stack outcome and #177 continuation repair |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced stale blocked DOC-002 state with completed archive state |
| `specs/doc-002-unified-landing-page-and-ia-shell` | Removed completed active spec folder |
| `.github/workflows/release.yml` | Durable release PR payload-sync fix |
| `tests/speckit-pro/layer1-structural/validate-release-workflow.sh` | Regression coverage for release PR payload-sync source |

## Feature Status

DOC-002 is complete and archived. DOC-003 and DOC-004 are the next actionable
interactive documentation specs.

## Constitution Compliance

PASS. DOC-002 cleanup is post-merge, provenance-backed, history-preserving, and
gated by recorded recovery commands. The concurrent release workflow fix is not
part of DOC-002 scope; it is included in this branch because PR #178 exposed a
release pipeline defect while post-spec hygiene was in progress.

## Outstanding Items

- Merge the durable release workflow fix before the next release-please PR is
  expected.
- Merge release PR #178 after its checks pass.
- Scaffold DOC-003 and/or DOC-004 from the refreshed roadmap state.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-002-unified-landing-page-and-ia-shell`
- blockedBy: None

## Defaults Applied

- No screenshot artifacts were committed.
- `.specify/feature.json` was absent and not recreated.
- Historical workflow/process artifacts under `docs/ai/specs/.process/` were
  retained as project execution history.

## Scoping

The cleanup removes only completed active SpecKit artifacts. The durable docs
site shell remains in `docs-site/`.
