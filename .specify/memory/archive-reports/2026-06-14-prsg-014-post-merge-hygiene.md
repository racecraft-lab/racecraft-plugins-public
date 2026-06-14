# Archival Report: PRSG-014 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/prsg-014-optional-gh-stack-stack-manager-integration` | merged | cleanup applied | PRSG-014 shipped through merged PR #181, provenance and recovery commands are recorded, stack-manager behavior lives in production scripts/contracts and committed tests, and no production or test script depends on the live spec folder |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed slash-command contract directly.
- Cleanup branch: `codex/post-merge-archive-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; PRSG-014 was archived after PR #181 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference |
|----|-------|-----------|--------------|----------------|
| #181 | `feat(speckit-pro): Add optional gh-stack stack manager integration` | 2026-06-14T20:40:02Z | `4b8342f42db3223db6955a1390b30949b8caea8c` | `ca39ded7975c93fc93217144121237b3295abce3` |

- Source spec path: `specs/prsg-014-optional-gh-stack-stack-manager-integration`
- Source workflow: `docs/ai/specs/.process/PRSG-014-workflow.md`
- Design concept: `docs/ai/specs/.process/PRSG-014-design-concept.md`
- Artifact manifest: `specs/prsg-014-optional-gh-stack-stack-manager-integration/SPEC-MOC.md`
- Canonical shipped behavior:
  - `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh`
  - `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
  - `speckit-pro/skills/speckit-autopilot/scripts/restack.sh`
  - `speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json`
- Release follow-up: PR #182 released `speckit-pro` v2.14.0 and PR #183 synced plugin marketplace payloads after PRSG-014 merged.
- Screenshot retention: N/A; verification evidence is shell and GitHub Checks output.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

PRSG-014 completed the optional stack-manager hardening lane for PR-size
governance. It added deterministic `gh stack` support detection, a shared
stack-manager decision schema, emission/restack evidence threading, fallback
before mutation, recoverable blocked-state behavior after partial stack-manager
mutation, and Claude/Codex operator-guidance parity.

The canonical fallback remains explicit GitHub base/head PR creation and edit
commands. `gh-stack` is opportunistic: missing, unsupported, ambiguous, unsafe,
or topology-incompatible environments fall back before mutation. Partial or
unknown `gh-stack` mutation blocks with recoverable state instead of switching
managers.

## Task Completion

- `tasks.md`: 71 / 71 implementation tasks checked complete.
- Checklists: requirements 16/16, integration 12/12, reliability 16/16,
  error-handling 16/16, security 15/15.
- Workflow gate G7 passed with implementation evidence recorded in
  `docs/ai/specs/.process/PRSG-014-workflow.md`.

## Recovery Commands

```text
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/research.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/data-model.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/quickstart.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/SPEC-MOC.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/contracts/stack-manager-decision.schema.json
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/requirements.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/integration.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/reliability.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/error-handling.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/checklists/security.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/pr-packet.md
git checkout 4b8342f42db3223db6955a1390b30949b8caea8c -- specs/prsg-014-optional-gh-stack-stack-manager-integration
```

## Pre-Cleanup Verification

- `gh pr view 181` confirmed PR #181 merged to `main` with merge commit
  `4b8342f42db3223db6955a1390b30949b8caea8c`.
- PR #181 checks were green: PR Checks `detect`, `validate-pr-title`,
  `test (speckit-pro)`, `validate-plugins`, and CodeQL.
- Workflow implementation evidence records:
  - `test-detect-stack-manager: 18/18`
  - `test-multi-pr-emission: 159/159`
  - `test-restack: 33/33`
  - Layer 1 `979/979`
  - Layer 4 `1768/1768`
  - Layer 7 all fixtures passed
  - Layer 8 `12/12`
  - default suite `2937/2937`
- Pre-cleanup `generate-spec-index.sh --check .` reported the active
  PRSG-014 `SPEC-MOC.md` generated zone stale, as expected before cleanup.

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated `docs/ai/specs/interactive-documentation-roadmap-MOC.md`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -c 'import json; json.load(open("docs/ai/specs/.process/autopilot-state.json"))'`
  passed.
- `find specs -mindepth 1 -maxdepth 2 -print` returned only `specs/.gitkeep`.
- `bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh`
  passed `18/18` after its PRSG-014 evidence writes were isolated to a temp
  repo root, and the active `specs` tree remained only `specs/.gitkeep`.
- `git worktree prune --verbose` removed the stale, prunable PRSG-014 worktree
  metadata entry whose gitdir pointed to a non-existent location.
- `gh pr list --state open` returned no open repository PRs.
- `git diff --check` passed.
- `bash tests/speckit-pro/run-all.sh` passed `2947/2947`.
  - Layer 1 structural: `551/551`.
  - Layer 1 Codex structural: `430/430`.
  - Layer 4 script unit: `1776/1776`.
  - Layer 5 tool scoping: `190/190`.

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled PRSG-014 feature record |
| `.specify/memory/plan.md` | Appended PRSG-014 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended PRSG-014 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added PRSG-014 archive cleanup note |
| `docs/ai/specs/pr-size-governance-technical-roadmap.md` | Marked PRSG-014 complete and archived |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Regenerated active SPEC index after cleanup |
| `docs/ai/specs/.process/PRSG-014-workflow.md` | Recorded merged PR and archive outcome |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced stale active PRSG-014 state with completed archive state |
| `tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh` | Isolated detector evidence writes to a temp repo root so post-archive tests do not recreate active spec artifacts |
| `specs/prsg-014-optional-gh-stack-stack-manager-integration` | Removed completed active spec folder |

## Feature Status

PRSG-014 is complete and archived. The PR-size governance roadmap has no
remaining active PRSG implementation specs.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. No generated screenshot artifacts are committed.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/prsg-014-optional-gh-stack-stack-manager-integration`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical workflow/process artifacts under `docs/ai/specs/.process/` were
  retained as project execution history.
