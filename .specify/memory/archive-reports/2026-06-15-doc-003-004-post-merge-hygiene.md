# Archival Report: DOC-003 and DOC-004 Post-Merge Hygiene

## Mode

- archiveMode: multi-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-003-claude-code-marketplace-installation-path` | merged | cleanup applied | DOC-003 shipped through merged PR #187, provenance and recovery commands are recorded, and the durable Claude install route lives in `docs-site/src/content/docs/install/claude-code.md` |
| `specs/doc-004-codex-marketplace-installation-path` | merged | cleanup applied | DOC-004 shipped through merged PR #186, provenance and recovery commands are recorded, and the durable Codex install route lives in `docs-site/src/content/docs/install/codex.md` |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly.
- Cleanup branch: `codex/doc-003-004-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-003 and DOC-004 were archived after both PRs merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| Spec | PR | Title | Merged at | Merge commit | Tree reference | Task completion |
|------|----|-------|-----------|--------------|----------------|-----------------|
| DOC-003 | #187 | `docs(DOC-003): add Claude Code install route` | 2026-06-15T20:26:31Z | `afc197a278001c7b8c2ffeb973c359971676d597` | `ef3e4eb22c286bafa1657e78c5461b774e8da1e6` | 39 / 39 |
| DOC-004 | #186 | `docs(DOC-004): add Codex marketplace installation path` | 2026-06-15T20:40:39Z | `bc48441c494d34a7df9876c3bdebabc4db8408a5` | `31c75c95d787ea2661216e29e6ec8b0a8ab19625` | 20 / 20 |

- Source spec paths:
  - `specs/doc-003-claude-code-marketplace-installation-path`
  - `specs/doc-004-codex-marketplace-installation-path`
- Source workflows:
  - `docs/ai/specs/.process/DOC-003-workflow.md`
  - `docs/ai/specs/.process/DOC-004-workflow.md`
- Artifact manifests:
  - `specs/doc-003-claude-code-marketplace-installation-path/SPEC-MOC.md`
  - `specs/doc-004-codex-marketplace-installation-path/SPEC-MOC.md`
- Canonical shipped docs:
  - `docs-site/src/content/docs/install/claude-code.md`
  - `docs-site/src/content/docs/install/codex.md`
- Screenshot retention: N/A; browser evidence was textual and route-render verification was completed before merge.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-003 and DOC-004 completed the platform-specific install tier for the
interactive documentation roadmap.

DOC-003 delivered a Claude Code install path covering Racecraft marketplace
add/install, `/reload-plugins`, `/plugin` visibility, namespaced
`/speckit-pro:*` verification, update, uninstall, marketplace removal, clean
reinstall, Claude-specific source/generated payload trust surfaces, and
install-facing skill terminology.

DOC-004 delivered a Codex install path covering repo-scoped, personal/local,
and CLI marketplace paths, generated Codex payload use, installed plugin cache
behavior, `$install` and `@SpecKit Pro -> install`, nine-file custom-agent TOML
verification, restart/rerun triggers, README and generated payload README
alignment, and bounded install-safety guidance.

## Task Completion

- DOC-003 `tasks.md`: 39 / 39 implementation tasks checked complete.
- DOC-004 `tasks.md`: 20 / 20 implementation tasks checked complete.
- No unchecked implementation tasks remained before cleanup.

## Recovery Commands

```text
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/spec.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/plan.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/tasks.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/research.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/data-model.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/quickstart.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/SPEC-MOC.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/checklists/accessibility.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/checklists/error-handling.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/checklists/requirements.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/checklists/security.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/checklists/ux.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/emission/state.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/emission/full-verification/verification.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/final-reviewability/gate-state.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packet/pr-body.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packet/pr-packet.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packets/pr-packet/validation.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/reviewability/hazard-route.json
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/.process/reviewability/tasks-gate.json
git checkout afc197a278001c7b8c2ffeb973c359971676d597 -- specs/doc-003-claude-code-marketplace-installation-path

git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/spec.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/plan.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/tasks.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/research.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/data-model.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/quickstart.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/SPEC-MOC.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/retrospective.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/verify-tasks-report.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/contracts/codex-install-content-contract.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/checklists/accessibility.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/checklists/error-handling.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/checklists/requirements.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/checklists/security.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/checklists/ux.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/.process/final-reviewability/gate-state.json
git checkout bc48441c494d34a7df9876c3bdebabc4db8408a5 -- specs/doc-004-codex-marketplace-installation-path
```

## Pre-Cleanup Verification

- `gh pr view 187` confirmed DOC-003 merged to `main` with merge commit
  `afc197a278001c7b8c2ffeb973c359971676d597`.
- `gh pr view 186` confirmed DOC-004 merged to `main` with merge commit
  `bc48441c494d34a7df9876c3bdebabc4db8408a5`.
- `rg "^- \[ \]"` found no unchecked tasks in either completed spec.
- Worktree state before archival edits was clean.

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated `docs/ai/specs/interactive-documentation-roadmap-MOC.md`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `find specs -mindepth 1 -maxdepth 2 -print` returned only `specs/.gitkeep`.
- `git worktree prune --dry-run --verbose` produced no stale worktree metadata.
- `git worktree prune --verbose` produced no stale worktree metadata.
- `git diff --check` passed.
- `pnpm --dir docs-site validate` passed with 0 Astro errors, 0 warnings, and
  0 hints; production build generated 12 pages and all internal links were
  valid.
- `pnpm --dir docs-site validate:links` passed; production build generated 12
  pages and all internal links were valid.
- `bash tests/speckit-pro/run-all.sh` passed `3001/3001`.
  - Layer 1 structural: `559/559`.
  - Layer 1 Codex structural: `430/430`.
  - Layer 4 script unit: `1822/1822`.
  - Layer 5 tool scoping: `190/190`.

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-003 and DOC-004 feature records |
| `.specify/memory/plan.md` | Appended DOC-003/DOC-004 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-003/DOC-004 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-003/DOC-004 archive cleanup note |
| `docs/traceability-interactive-documentation.md` | Marked DOC-003 and DOC-004 completed and next tier ready |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-003 and DOC-004 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-003 and DOC-004 archived and DOC-005/DOC-006/DOC-007 ready |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed roadmap status and regenerated active-spec index after cleanup |
| `docs/ai/specs/.process/DOC-003-workflow.md` | Recorded merged PR and archive outcome |
| `docs/ai/specs/.process/DOC-004-workflow.md` | Recorded merged PR and archive outcome |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced stale active DOC-004 state with completed DOC-003/DOC-004 archive state |
| `specs/doc-003-claude-code-marketplace-installation-path` | Removed completed active spec folder |
| `specs/doc-004-codex-marketplace-installation-path` | Removed completed active spec folder |

## Feature Status

DOC-003 and DOC-004 are complete and archived. DOC-005, DOC-006, and DOC-007
are the next ready interactive documentation specs.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. No generated screenshot artifacts are committed.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-003-claude-code-marketplace-installation-path specs/doc-004-codex-marketplace-installation-path`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical workflow/process artifacts under `docs/ai/specs/.process/` were
  retained as project execution history.

## Scoping

The cleanup removes only completed active SpecKit artifacts. The shipped docs
site pages remain in `docs-site/`.
