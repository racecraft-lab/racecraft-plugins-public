# Archival Report: DOC-007 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-007-command-workflow-manifest-and-file-layout-reference` | merged | cleanup applied | DOC-007 shipped through merged PR #208; canonical durable artifacts live in the generated reference pages and reference generator under `docs-site/`; residual tracked content under `specs/**` was completed specification, planning, task, checklist, and contract evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly.
- Cleanup branch: `codex/doc-007-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-007 was archived after PR #208 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #208 | `docs(DOC-007): add generated reference pages` | 2026-06-17T20:17:55Z | `2f5ee096e903723e1ab0133c699bda5a22ae2172` | `67d3b8890b09605150b9cf300543d7a7ba517045` | generated reference pages, reference-page generator, reference checks, docs validation integration, linked documentation updates, and PR review remediation |

- Source spec path:
  - `specs/doc-007-command-workflow-manifest-and-file-layout-reference`
- Source workflow:
  - `docs/ai/specs/.process/DOC-007-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/DOC-007-design-concept.md`
- Canonical shipped docs and validation:
  - `docs-site/scripts/generate-reference-pages.mjs`
  - `docs-site/src/content/docs/reference.md`
  - `docs-site/src/content/docs/reference/skills.md`
  - `docs-site/src/content/docs/reference/agents.md`
  - `docs-site/src/content/docs/reference/manifests.md`
  - `docs-site/src/content/docs/reference/hooks.md`
  - `docs-site/src/content/docs/reference/scripts.md`
  - `docs-site/src/content/docs/reference/tests.md`
  - `docs-site/src/content/docs/reference/source-vs-dist.md`
  - `docs-site/package.json`
  - `docs-site/astro.config.mjs`
- Screenshot retention: N/A for the archive cleanup; no new browser UAT evidence is produced by this post-merge hygiene step.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-007 completed the generated reference library for the interactive
documentation roadmap. It added deterministic reference generation for skills,
agents, manifests, hooks, scripts, tests, and source-vs-dist layout; integrated
reference checks into docs validation; deep-linked existing docs routes into
the generated reference pages; and separated source facts from inferred notes
so users, maintainers, and agents can inspect exact plugin surfaces without
re-reading the repository tree.

This cleanup also adds the repeatable `speckit-archive-cleanup` plugin skill so
future post-merge SpecKit archive hygiene can be invoked directly from the
plugin instead of reconstructed from prior reports.

## Recovery Commands

```text
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/plan.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/tasks.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/SPEC-MOC.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-generator.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-inventory.schema.json
git checkout 2f5ee096e903723e1ab0133c699bda5a22ae2172 -- specs/doc-007-command-workflow-manifest-and-file-layout-reference
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-007 feature record |
| `.specify/memory/plan.md` | Appended DOC-007 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-007 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-007 archive cleanup note |
| `docs/traceability-interactive-documentation.md` | Marked DOC-007 completed and DOC-008/DOC-009 ready |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-007 archived and downstream docs specs ready |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-007 archived and downstream docs specs ready |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed roadmap status and generated index |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active DOC-007 state with completed archive state |
| `specs/doc-007-command-workflow-manifest-and-file-layout-reference` | Removed residual tracked specification and planning evidence |
| `speckit-pro/skills/speckit-archive-cleanup/SKILL.md` | Added Claude Code archive cleanup skill |
| `speckit-pro/codex-skills/speckit-archive-cleanup/SKILL.md` | Added Codex archive cleanup skill |
| `speckit-pro/codex-skills/speckit-archive-cleanup/agents/openai.yaml` | Added Codex skill picker metadata |
| `tests/speckit-pro/layer1-structural/validate-skills.sh` | Added the new Claude Code skill to structural validation |
| `tests/speckit-pro/layer1-structural/validate-codex-skills.sh` | Added the new Codex skill and policy expectations |
| `docs-site/scripts/generate-reference-pages.mjs` | Added skill-specific prerequisite and expected-artifact text |
| `docs-site/src/content/docs/reference/skills.md` | Refreshed generated skills reference |
| `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` | Refreshed generated plugin payloads after adding the skill |

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated `interactive-documentation-roadmap-MOC.md` after the active
  DOC-007 spec folder was removed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`
  after cleanup.
- `bash scripts/build-plugin-payloads.sh` rebuilt `dist/claude/speckit-pro`
  and `dist/codex/speckit-pro` after adding the archive cleanup skill.
- `pnpm --dir docs-site reference:generate` generated 7 reference pages.
- `pnpm --dir docs-site reference:check` passed.
- `git diff --check` passed.
- `pnpm --dir docs-site validate` passed with 0 Astro errors, 0 warnings, and
  0 hints; production build generated 19 pages and all internal links were
  valid.
- `pnpm --dir docs-site validate:links` passed; production build generated 19
  pages and all internal links were valid.
- `bash tests/speckit-pro/run-all.sh` passed `3041/3041`.
  - Layer 1 structural: `573/573`.
  - Layer 1 Codex structural: `451/451`.
  - Layer 4 script unit: `1827/1827`.
  - Layer 5 tool scoping: `190/190`.

`pnpm --dir docs-site install --frozen-lockfile` was required because
`docs-site/node_modules` was absent. The first sandboxed install hit
`ENOTFOUND registry.npmjs.org`; the escalated frozen-lockfile install completed
without modifying the lockfile.

## Feature Status

DOC-007 is complete and archived. DOC-008 and DOC-009 are the next ready
interactive documentation specs. DOC-010 remains sequenced after the remaining
content specs and docs hardening prerequisites.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. No generated screenshot artifacts are committed.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-007-command-workflow-manifest-and-file-layout-reference`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence outside active `specs/**` was retained.
- The merged DOC-007 active spec path contained complete specification,
  planning, task, checklist, and contract evidence; the archive records
  recovery commands before removing that active source folder.

## Scoping

The cleanup removes only completed DOC-007 planning evidence from active
`specs/**`. The shipped generated reference pages, generator, docs validation,
and linked documentation updates remain in `docs-site/`.
