# Archival Report: DOC-006 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-006-safe-interactive-selector-and-validation-aids` | merged | cleanup applied | DOC-006 shipped through merged PR #203; canonical durable docs live in `docs-site/src/content/docs/choose-your-path.mdx`, `docs-site/src/components/SafeInstallAids.astro`, `docs-site/src/data/safe-install-aids.ts`, and `docs-site/scripts/validate-doc006-safe-aids.mjs`; residual tracked content under `specs/**` was workflow, PR-packet, and reviewability evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly.
- Cleanup branch: `codex/doc-006-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-006 was archived after PR #203 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #203 | `docs(DOC-006): Add safe interactive selector and validation aids` | 2026-06-17T16:04:35Z | `973e9cf76143efe168f4c2b9ab5682581317e28c` | `a2678d1cd8d8ef6591d68a98c0279cfc6fcfacc7` | choose-your-path selector/checker aids, source-derived metadata helper, focused validation, review evidence, and manual UAT remediation |

- Source spec path:
  - `specs/doc-006-safe-interactive-selector-and-validation-aids`
- Source workflow:
  - `docs/ai/specs/.process/DOC-006-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/DOC-006-design-concept.md`
- Canonical shipped docs and validation:
  - `docs-site/src/content/docs/choose-your-path.mdx`
  - `docs-site/src/components/SafeInstallAids.astro`
  - `docs-site/src/data/safe-install-aids.ts`
  - `docs-site/scripts/validate-doc006-safe-aids.mjs`
- Screenshot retention: N/A; browser UAT evidence was handled through PR review comments and remediation rather than committed screenshots.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-006 completed the safe interactive aid tier for the interactive documentation
roadmap. It enhances the existing choose-your-path route with static-first
platform and install-scope selector guidance, copyable command blocks,
repository-only manifest consistency checks, an accessible generated payload
diagram, first-run checkpoints, lightweight troubleshooting handoffs, and
focused validation that protects platform command boundaries and browser safety.

## Recovery Commands

```text
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/plan.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/tasks.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/SPEC-MOC.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/contracts/doc006-safe-aids.schema.json
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/verify-report.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/uat-runbook.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/pr-body.md
git checkout 973e9cf76143efe168f4c2b9ab5682581317e28c -- specs/doc-006-safe-interactive-selector-and-validation-aids
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-006 feature record |
| `.specify/memory/plan.md` | Appended DOC-006 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-006 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-006 archive cleanup note |
| `docs/traceability-interactive-documentation.md` | Marked DOC-006 completed and archived |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-006 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-006 archived and updated DOC-010 readiness |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed roadmap status and generated index |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active DOC-006 state with completed archive state |
| `specs/doc-006-safe-interactive-selector-and-validation-aids` | Removed residual tracked workflow and PR-packet evidence |

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated `interactive-documentation-roadmap-MOC.md` after the active
  DOC-006 spec folder was removed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`
  after cleanup.
- `git worktree prune --dry-run --verbose` first identified stale DOC-005
  worktree metadata; `git worktree prune --verbose` removed those stale entries;
  a final dry-run produced no stale metadata output.
- `git diff --check` passed.
- `node docs-site/scripts/validate-doc006-safe-aids.mjs` passed.
- `pnpm --dir docs-site install --frozen-lockfile` was required because
  `docs-site/node_modules` was absent; the first sandboxed install hit
  `ENOTFOUND registry.npmjs.org`, then the escalated frozen-lockfile install
  completed without modifying the lockfile.
- `pnpm --dir docs-site validate` passed with 0 Astro errors, 0 warnings, and
  0 hints; production build generated 12 pages and all internal links were
  valid.
- `pnpm --dir docs-site validate:links` passed; production build generated 12
  pages and all internal links were valid.
- `bash tests/speckit-pro/run-all.sh` passed `3009/3009`.
  - Layer 1 structural: `561/561`.
  - Layer 1 Codex structural: `432/432`.
  - Layer 4 script unit: `1826/1826`.
  - Layer 5 tool scoping: `190/190`.

## Feature Status

DOC-006 is complete and archived. DOC-007 is the next ready interactive
documentation spec, and DOC-010 is unblocked by the completed DOC-006 safe
interactive aids.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. No generated screenshot artifacts are committed.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-006-safe-interactive-selector-and-validation-aids`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence outside active `specs/**` was retained.
- The merged DOC-006 active spec path contained complete specification,
  planning, task, reviewability, PR-packet, UAT, and retrospective evidence; the
  archive records recovery commands before removing that active source folder.

## Scoping

The cleanup removes only completed DOC-006 process evidence from active
`specs/**`. The shipped choose-your-path route, safe install aids component,
source-derived metadata helper, and focused validation script remain in
`docs-site/`.
