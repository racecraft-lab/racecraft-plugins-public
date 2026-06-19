# Archival Report: DOC-010 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-010-search-accessibility-deep-links-docs-validation` | merged | cleanup applied | DOC-010 shipped through merged PRs #232 through #236. Canonical durable content now lives in the docs-site validation path, PR Checks docs gate, compact Playwright smoke coverage, accessible interactive-aid docs, and process records; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |
| TACD completed work | already archived | no-op | TACD-001, TACD-002, and TACD-003 were already archived by prior cleanup reports. No active TACD spec directory exists on `origin/main`. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/archive-doc-tacd-completed-work`, based on updated `origin/main`
- Cleanup PR: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/237`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-010 was archived after PRs #232 through #236 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #232 | `docs(DOC-010): Add docs-site validation foundation` | 2026-06-19T20:09:48Z | `699c54bda562d6c900a306d4838b97d9f6ddbcf8` | `4babe109cd87cc5a906f006b8355dfb06cfb9da3` | docs-site validation command foundation, package scripts, quality validator, Playwright config, and smoke scaffold |
| #233 | `docs(DOC-010): Update Find And Share Support Guidance` | 2026-06-19T20:16:03Z | `6f88b0b8a7f38869e5e7fc78c507a580dd92b998` | `148133bb9448d13e4e2d7a5a8ceb18766c0133e4` | support anchor inventory, glossary/search guidance, generated reference and release workflow deep-link validation |
| #234 | `docs(DOC-010): Update Use Interactive Aids Accessibly` | 2026-06-19T20:24:35Z | `b3c0eb5e5b281df94f5e03861a65674ec291e0a1` | `418bc613e0a90a5b14edffe7ac066337ca8835f1` | accessible `SafeInstallAids` and `LifecycleFlow` behavior, static fallback content, and focused safe-aids validation |
| #235 | `docs(DOC-010): Update Run One Matching Docs Validation Path` | 2026-06-19T20:32:31Z | `abd7f2343b6a723cfe7bca806ce17dba96657141` | `2e662e61ca0f760fa7baad55d34cc896f28f1221` | combined local docs validation path and conditional `validate-docs` PR Checks gate |
| #236 | `docs(DOC-010): Update Review Minimal Browser Evidence` | 2026-06-19T20:46:22Z | `3fb8b55fc13b3896f7a9507eb07fa40b077f8781` | `bd1b9df9e41e99bbb201a9712868b9d8ec714029` | desktop/mobile route smoke, search/deep-link/interactive assertions, compact smoke artifact upload, and final PR packet evidence |

- Source spec path:
  - `specs/doc-010-search-accessibility-deep-links-docs-validation`
- Source workflow:
  - `docs/ai/specs/.process/DOC-010-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/DOC-010-design-concept.md`
- Canonical shipped artifacts:
  - `docs-site/package.json`
  - `docs-site/pnpm-lock.yaml`
  - `docs-site/playwright.config.mjs`
  - `docs-site/tests/docs-smoke.spec.mjs`
  - `docs-site/scripts/validate-docs-quality.mjs`
  - `docs-site/scripts/validate-doc006-safe-aids.mjs`
  - `docs-site/src/content/docs/glossary.md`
  - `docs-site/src/content/docs/choose-your-path.mdx`
  - `docs-site/src/components/LifecycleFlow.astro`
  - `.github/workflows/pr-checks.yml`
- CI evidence:
  - PR #236 checks passed after conflict resolution: CodeQL, Analyze actions/javascript-typescript/python, detect, validate-pr-title, test (speckit-pro), validate-docs, and validate-plugins.
  - PR Checks run: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27847320866`
  - CodeQL runs: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27847319470`, `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27847319569`
- Screenshot retention: DOC-010 smoke evidence is a GitHub Actions artifact named `docs-site-smoke-evidence` with 7-day retention when smoke artifacts exist.
- Expiration risk: Low for committed artifacts; GitHub Actions logs and smoke artifacts may expire according to GitHub retention policy.

## Feature Summary

DOC-010 completed the final interactive documentation quality hardening slice.
It keeps the existing Astro/Starlight and Starlight/Pagefind search path, adds
stable support anchors and deep-link validation, improves glossary and
support-oriented findability, extends accessible interactive-aid behavior and
static fallbacks, and adds deterministic docs-site validation for generated
references, safe aids, support anchors, source-update guidance, link/build
coverage, and compact browser smoke.

The feature also adds one local docs validation path through
`pnpm --dir docs-site validate`, exposes a matching conditional `validate-docs`
PR Checks job with job-level changed-file detection, preserves plugin matrix
semantics for plugin-only changes, and publishes compact reviewer smoke
evidence for six logical routes across desktop and mobile.

Together with the previously archived DOC-001 through DOC-009 work, DOC-010
completes the interactive documentation roadmap. The active DOC spec folder can
leave `specs/**` because canonical behavior and docs now live in committed
docs-site, validation, workflow, roadmap, memory, and archive-report paths.

## Recovery Commands

```text
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/plan.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/tasks.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/SPEC-MOC.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/research.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/data-model.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/quickstart.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/contracts/browser-smoke-contract.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/contracts/docs-validation-contract.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/contracts/pr-checks-docs-gate-contract.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs/ai/specs/.process/DOC-010-workflow.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs/ai/specs/.process/DOC-010-design-concept.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs-site/scripts/validate-docs-quality.mjs
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs-site/tests/docs-smoke.spec.mjs
git checkout 3fb8b55fc13b3896f7a9507eb07fa40b077f8781 -- specs/doc-010-search-accessibility-deep-links-docs-validation
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-010 feature record |
| `.specify/memory/plan.md` | Appended DOC-010 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-010 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-010 archive cleanup note and active docs-site validation context |
| `docs/traceability-interactive-documentation.md` | Marked DOC-010 completed and the DOC roadmap archived |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-010 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-010 completed and the interactive documentation roadmap archived |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Replaced active DOC-010 spec link with archive/report guidance |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Cleared stale generated DOC active-spec index rows after the shared generator refresh |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active DOC-010 state with completed archive state |
| `specs/doc-010-search-accessibility-deep-links-docs-validation` | Removed residual active spec evidence |

## Post-Cleanup Verification

- PASS: `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- PASS: `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`.
- PASS: stale active DOC-010 path scan found only intentional archive, memory,
  and recovery-command references.
- PASS: `git diff --check`
- PASS: `bash tests/speckit-pro/run-all.sh`
  - `speckit-pro test suite: 3163/3163 passed`
  - `L1: 573/573`
  - `L1: 451/451`
  - `L4: 1949/1949`
  - `L5: 190/190`

## Feature Status

DOC-010 is complete and archived. DOC-001 through DOC-010 are now complete and
archived, so the interactive documentation roadmap is feature complete for the
planned v1 sequence. TACD-001 through TACD-003 were already archived; TACD-004
remains ready to scaffold from the archived TACD artifacts.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. DOC-010 behavior remains in committed docs-site,
validation, and PR Checks artifacts. No plugin runtime behavior, manifest
version, marketplace metadata, or generated payload semantics is changed by
this archive cleanup.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-010-search-accessibility-deep-links-docs-validation`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- Existing TACD archive reports were treated as authoritative because no active
  TACD spec directory remains on `origin/main`.
- The merged DOC-010 active spec path contained specification, planning,
  contract, checklist, reviewability, verification, MOC, and task evidence;
  this archive records recovery commands before removing that active source
  folder.

## Scoping

The cleanup removes only completed DOC-010 process/spec evidence from active
`specs/**`. The shipped docs-site validation path, support anchors,
accessibility/fallback updates, PR Checks docs gate, compact smoke evidence
contract, workflow file, design concept, roadmap, memory entries, and archive
report remain in durable repository paths.
