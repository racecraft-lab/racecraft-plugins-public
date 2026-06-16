# Archival Report: DOC-005 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer` | merged | cleanup applied | DOC-005 shipped through merged PRs #198-#201; canonical durable docs live in `docs-site/src/content/docs/first-run.md`, `docs-site/src/content/docs/spec-kit-lifecycle.mdx`, and `docs-site/src/components/LifecycleFlow.astro`; residual tracked content under `specs/**` was PR-packet evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly.
- Cleanup branch: `codex/doc-005-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean after moving the untracked `.playwright-mcp/` Browser artifact to `/private/tmp/racecraft-playwright-mcp-doc005-hygiene-eb0c`
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-005 was archived after PRs #198-#201 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #198 | `docs(DOC-005): Record DOC-005 validation evidence` | 2026-06-16T18:09:34Z | `238bd36921787588f52d5f0f24bd3a0d7b485d66` | `6f098af3452d8c935c67622e5acfa34ae86328f0` | command validation and scope evidence |
| #199 | `docs(DOC-005): Document the first successful run tutorial` | 2026-06-16T18:11:19Z | `d6143d8fdf142f277b525a8fb759ee8b10faa44e` | `e7e392f897853ce206ab6b8aaf470a4481b4e04b` | first-run route and review evidence |
| #200 | `docs(DOC-005): Document the SpecKit lifecycle explainer` | 2026-06-16T20:28:36Z | `f03e352d5cc143d104c9b8f977266496fa869fd4` | `cec126592fcaf5a71325f73bebc6c839377edcc5` | lifecycle route, static component, accessibility/static review evidence |
| #201 | `docs(DOC-005): Add prerequisite checks and fallback handoffs` | 2026-06-16T20:47:28Z | `0f0eff05f80130d4c61cc91c2633f2b73ad88151` | `8bbf7ea908e30407a2d67a5fb25d3ed60a04c336` | prerequisite checks and bounded fallback evidence |

- Source spec path:
  - `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer`
- Source workflow:
  - The merged `main` tip did not contain `docs/ai/specs/.process/DOC-005-workflow.md`; this hygiene run treated the retained PR-packet evidence as the active cleanup target.
- Canonical shipped docs:
  - `docs-site/src/content/docs/first-run.md`
  - `docs-site/src/content/docs/spec-kit-lifecycle.mdx`
  - `docs-site/src/components/LifecycleFlow.astro`
- Artifact manifest:
  - `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/scope.md`
- Screenshot retention: N/A; DOC-005 browser/UAT evidence was recorded as text review packets rather than committed screenshots.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-005 completed the first-run activation tier for the interactive
documentation roadmap. It teaches users to start from the correct platform
install route, define first success as artifacts plus validation evidence,
inspect prerequisites before scaffolding, use platform-specific command syntax,
follow the idea-to-PRD-to-roadmap-to-scaffold-to-autopilot trail, and interpret
Spec Kit lifecycle phases and gates through static accessible content.

## Recovery Commands

```text
git show 238bd36921787588f52d5f0f24bd3a0d7b485d66:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/command-validation.md
git show 238bd36921787588f52d5f0f24bd3a0d7b485d66:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/scope.md
git show d6143d8fdf142f277b525a8fb759ee8b10faa44e:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/first-run-review.md
git show d6143d8fdf142f277b525a8fb759ee8b10faa44e:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/first-run-snippet-review.md
git show f03e352d5cc143d104c9b8f977266496fa869fd4:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/lifecycle-accessibility-review.md
git show f03e352d5cc143d104c9b8f977266496fa869fd4:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/lifecycle-static-review.md
git show 0f0eff05f80130d4c61cc91c2633f2b73ad88151:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/bounded-fallback-review.md
git show 0f0eff05f80130d4c61cc91c2633f2b73ad88151:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/platform-separation-review.md
git checkout 0f0eff05f80130d4c61cc91c2633f2b73ad88151 -- specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-005 feature record |
| `.specify/memory/plan.md` | Appended DOC-005 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-005 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-005 archive cleanup note |
| `docs/traceability-interactive-documentation.md` | Marked DOC-005 completed and archived |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-005 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-005 archived and DOC-006/DOC-007 ready |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed roadmap status |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced stale DOC-003/DOC-004 archive state with completed DOC-005 archive state |
| `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer` | Removed residual tracked PR-packet evidence |

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  reported the index current with no map regeneration needed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`
  after cleanup.
- `git worktree prune --dry-run --verbose` first identified stale DOC-003 and
  DOC-004 worktree metadata; `git worktree prune --verbose` removed both stale
  entries; a final dry-run produced no stale metadata output.
- `git diff --check` passed.
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

DOC-005 is complete and archived. DOC-006 and DOC-007 are the next ready
interactive documentation specs.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. No generated screenshot artifacts are committed.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence outside active `specs/**` was retained.
- The merged DOC-005 active spec path had residual PR-packet files but no
  `spec.md`, `plan.md`, or `tasks.md`; the archive records that drift instead
  of inventing missing raw artifacts.

## Scoping

The cleanup removes only completed DOC-005 process evidence from active
`specs/**`. The shipped docs site pages and static lifecycle component remain
in `docs-site/`.
