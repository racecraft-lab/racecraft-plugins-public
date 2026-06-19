# Archival Report: TACD-003 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/tacd-003-prerequisite-and-documentation-messaging` | merged | cleanup applied | TACD-003 shipped through merged PR #230. The durable behavior now lives in source guidance, generated payloads, focused tests, and process records; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/tacd-003-archive-cleanup`, based on updated `origin/main`
- Cleanup PR: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/231`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; TACD-003 was archived after PR #230 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #230 | `feat(speckit-pro): TACD-003 prerequisite advisory, active guidance, focused verification, and review packet evidence` | 2026-06-19T14:41:09Z | `bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9` | `6aea1266ff75fef87b94fb5aac3bf6a5aa5d58e6` | prerequisite advisory behavior, active guidance, focused verification, generated payload refresh, and PR packet evidence |

- Source spec path:
  - `specs/tacd-003-prerequisite-and-documentation-messaging`
- Source workflow:
  - `docs/ai/specs/.process/TACD-003-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/TACD-003-design-concept.md`
- Canonical shipped artifacts:
  - `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
  - `speckit-pro/skills/speckit-autopilot/references/prerequisites.md`
  - `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`
  - `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`
  - `speckit-pro/skills/speckit-coach/references/autopilot-guide.md`
  - `speckit-pro/skills/speckit-autopilot/SKILL.md`
  - `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
  - `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
  - `tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh`
  - `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`
  - `dist/claude/speckit-pro/`
  - `dist/codex/speckit-pro/`
- CI evidence:
  - PR #230 checks passed: CodeQL, Analyze actions/javascript-typescript/python, detect, validate-pr-title, test (speckit-pro), and validate-plugins.
  - PR Checks run: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27832129612`
  - CodeQL runs: `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27832127770`, `https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27832127833`
- Screenshot retention: N/A; TACD-003 changed shell behavior, guidance, generated payloads, and tests, not visual UI.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

TACD-003 replaces SpecKit Pro's named optional MCP prerequisite inventory with a
single successful `capability_coverage` advisory. The advisory names codebase
context, library documentation, web or domain research, and source extraction as
capability categories, keeps missing optional capability resources non-blocking
when acceptable fallback evidence exists, and preserves true prerequisite
failures as actionable blockers.

The feature also updates active Claude and Codex prerequisite guidance, plugin
limitation guidance, coach/autopilot wording, generated payload copies, and
focused Layer 4 assertions so user-facing setup and documentation no longer
teach a fixed optional tool set. TACD-004 remains responsible for deterministic
static enforcement and eval coverage.

## Recovery Commands

```text
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/spec.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/plan.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/SPEC-MOC.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/research.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/quickstart.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/checklists/error-handling.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/checklists/integration.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/checklists/reliability.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/checklists/requirements.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/.process/reviewability/atomicity-route.json
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/.process/reviewability/tasks-gate.json
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:docs/ai/specs/.process/TACD-003-workflow.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:docs/ai/specs/.process/TACD-003-design-concept.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh
git checkout bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9 -- specs/tacd-003-prerequisite-and-documentation-messaging
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled TACD-003 feature record |
| `.specify/memory/plan.md` | Appended TACD-003 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended TACD-003 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added TACD-003 archive cleanup note |
| `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` | Marked TACD-003 archived and TACD-004 ready to scaffold |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Replaced active TACD-003 spec link with archive/report guidance |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed generated spec index output after active spec cleanup |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active TACD-003 state with completed archive state |
| `specs/tacd-003-prerequisite-and-documentation-messaging` | Removed residual active spec evidence |

## Post-Cleanup Verification

- PASS: `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- PASS: `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`.
- PASS: stale active spec path scan found only intentional archive, memory, and
  recovery-command references.
- PASS: `git diff --check`
- PASS: `bash tests/speckit-pro/run-all.sh`
  - `speckit-pro test suite: 3163/3163 passed`
  - `L1: 573/573`
  - `L1: 451/451`
  - `L4: 1949/1949`
  - `L5: 190/190`

## Feature Status

TACD-003 is complete and archived. TACD-004 is unblocked and ready to scaffold
from the archived platform mechanics, active runtime guidance, and prerequisite
messaging work.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. TACD-003 behavior changes remain in committed
source/generator/test artifacts; TACD-004 deterministic enforcement remains a
separate roadmap spec.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/tacd-003-prerequisite-and-documentation-messaging`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- The merged TACD-003 active spec path contained specification, planning,
  checklist, reviewability, MOC, and task evidence; this archive records
  recovery commands before removing that active source folder.

## Scoping

The cleanup removes only completed TACD-003 process/spec evidence from active
`specs/**`. The prerequisite advisory behavior, active guidance, generated
payloads, focused tests, workflow file, design concept, roadmap, and archive
report remain in durable repository paths.
