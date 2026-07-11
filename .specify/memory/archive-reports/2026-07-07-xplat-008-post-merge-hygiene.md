# Archival Report - XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

## Mode
- **archiveMode**: single-feature cleanup from `XPLAT`
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup XPLAT`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-008-claude-codex-cutover-universal-install-release-gate` | eligibleForArchive -> archived | removed (cleanup applied) | XPLAT-008 merged across PRs #289, #290, #291, and readiness fix #292; active runtime cutover, payload rebuilds, public claim alignment, release-readiness gates, and safe repair controls now live outside active `specs/**` |

## Excluded Current Spec
`None` (XPLAT-008 implementation and readiness-fix PRs are merged; cleanup runs from `origin/main` on `codex/xplat-008-archive-cleanup`)

## Provenance
| PR | Title | Merged at | Merge commit | Head branch |
|----|-------|-----------|--------------|-------------|
| [#289](https://github.com/racecraft-lab/racecraft-plugins-public/pull/289) | `feat(speckit-pro): Update Active Installed-Runtime Surface Cutover` | `2026-07-07T00:54:54Z` | `59c18b2dcf79284182f6f5932e61716db0d58090` | `codex/xplat-008-review/01-us1` |
| [#290](https://github.com/racecraft-lab/racecraft-plugins-public/pull/290) | `feat(speckit-pro): Update Payload, Release, and Public Docs Gates` | `2026-07-07T01:14:33Z` | `1793128875dd0a31e9fafd606eaa55e92123d63e` | `codex/xplat-008-review/02-us2` |
| [#291](https://github.com/racecraft-lab/racecraft-plugins-public/pull/291) | `feat(speckit-pro): Update Native UAT, Update, and Safe Repair` | `2026-07-07T01:25:47Z` | `66defab977c166bff8726724cdb728b95eec0165` | `codex/xplat-008-review/03-us3` |
| [#292](https://github.com/racecraft-lab/racecraft-plugins-public/pull/292) | `fix(release): unblock XPLAT-008 readiness gate` | `2026-07-07T02:00:33Z` | `9507fd452a3e344c1912b449f3bb4f2c38437b38` | `codex/fix-main-release-ci` |

- **Source spec path**: `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/` (repo-relative)
- **Workflow file**: `docs/ai/specs/.process/XPLAT-008-workflow.md`
- **Design concept**: `docs/ai/specs/.process/XPLAT-008-design-concept.md`
- **Preserved release packet**: `docs/ai/specs/.process/XPLAT-008-release-readiness.md`
- **Preserved UAT matrix**: `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
- **Preserved partial UAT detail**: `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md`
- **Base branch**: `main`
- **CI run URL**: N/A - merge commits are durable source references
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Expiration risk**: None for committed repository state; release/UAT process evidence is preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-008 shipped the final cross-platform runtime implementation lane for
SpecKit Pro's installed Claude and Codex plugin paths. The merged stack cut
active installed-runtime guidance over to direct Python runner invocation,
rebuilt generated Claude and Codex payloads from source, aligned public docs and
README claims to implemented controls, added payload completeness and
release-readiness gates, added native UAT matrix validation, added update and
install-health repair blockers, and implemented bounded checksum-backed repair
behavior for trusted installed-cache gaps.

The feature is intentionally archived as a blocked release-readiness packet.
Public native Windows/macOS/Linux support claims remain blocked until all six
native operator UAT rows pass in
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md` and the release-readiness gate
is rerun against that evidence.

## Canonical Artifacts
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/install_inventory.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `speckit-pro/skills/**`
- `speckit-pro/codex-skills/**`
- `speckit-pro/hooks/hooks.json`
- `speckit-pro/codex-hooks.json`
- `speckit-pro/agents/gate-validator.md`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/update-and-rollback.md`
- `docs-site/src/content/docs/first-run.md`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs/ai/specs/.process/XPLAT-008-workflow.md`
- `docs/ai/specs/.process/XPLAT-008-design-concept.md`
- `docs/ai/specs/.process/XPLAT-008-release-readiness.md`
- `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
- `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md`
- `tests/speckit-pro/unit/fixtures/installed-plugin-release/`
- `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/`
- `tests/speckit-pro/unit/test-speckit-pro-gates.py`

## Recovery Commands
```text
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/plan.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/tasks.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/research.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/data-model.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/quickstart.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/SPEC-MOC.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/payload-completeness.schema.json
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/release-readiness.schema.json
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/uat-matrix.schema.json
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/install-health-repair.schema.json
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/contracts/runner-invocation.schema.json
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/release-readiness.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat/codex-macos.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-workflow.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-design-concept.md
git checkout 9507fd452a3e344c1912b449f3bb4f2c38437b38 -- specs/xplat-008-claude-codex-cutover-universal-install-release-gate
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-008 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-008 product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-008 technical approach, verification strategy, and cleanup note |
| `.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-008 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-008 archived and public release held by UAT matrix |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-008 link with archive and preserved-evidence pointers |
| `docs/ai/specs/.process/autopilot-state.json` | Marked XPLAT-008 as post-merge archived state |
| `docs/ai/specs/.process/XPLAT-008-release-readiness.md` | Preserved release-readiness packet outside active `specs/**` |
| `docs/ai/specs/.process/XPLAT-008-uat-matrix.md` | Preserved UAT matrix outside active `specs/**` |
| `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` | Preserved partial Codex/macOS UAT detail outside active `specs/**` |
| `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/` | Preserved XPLAT-008 contract schemas needed by Layer 4 gate coverage after cleanup |
| `tests/speckit-pro/unit/fixtures/installed-plugin-release/release-readiness-cases.json` | Repointed release-readiness fixture evidence to preserved process paths |
| `tests/speckit-pro/unit/fixtures/installed-plugin-release/uat-matrix-cases.json` | Repointed UAT matrix fixture evidence to preserved process paths |
| `tests/speckit-pro/unit/test-speckit-pro-gates.py` | Repointed XPLAT-008 contract reads away from active `specs/**` |
| `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | Added regression coverage for same-repo Git worktree metadata names during branch detection |
| `tests/speckit-pro/unit/test-speckit-pro-runner.py` | Removed the archived XPLAT-008 spec path from active-path guard allow-list coverage |
| `speckit-pro/speckit_pro_runner/gates/release.py` | Repointed default XPLAT-008 UAT evidence references to preserved process files |
| `speckit-pro/speckit_pro_runner/helpers/read_only.py` | Accepted same-repo `.git/worktrees/<id>` metadata when resolving read-only helper branch state |
| `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | Refreshed runner source metadata after helper branch-detection fix |
| `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | Refreshed runner source checksums after helper branch-detection fix |
| `dist/claude/speckit-pro/speckit_pro_runner/` | Rebuilt generated payload runner files after source metadata refresh |
| `dist/codex/speckit-pro/speckit_pro_runner/` | Rebuilt generated payload runner files after source metadata refresh |
| `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `python3 -m json.tool tests/speckit-pro/unit/fixtures/installed-plugin-release/release-readiness-cases.json`
- `python3 -m json.tool tests/speckit-pro/unit/fixtures/installed-plugin-release/uat-matrix-cases.json`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `python3 tests/speckit-pro/unit/test-speckit-pro-gates.py`
- `python3 tests/speckit-pro/unit/test-speckit-pro-runner.py`
- `python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py --helper check-prerequisites`
- `node docs-site/scripts/generate-reference-pages.mjs --check`
- `git diff --check`
- `bash tests/speckit-pro/run-all.sh`

Result: PASS. JSON parse checks passed, the SpecKit index is current, active
`specs/**` contains only `specs/.gitkeep`, docs reference pages are current,
focused gate tests passed (`47/47`), focused runner tests passed (`10/10`),
focused read-only `check-prerequisites` tests passed (`33/33`), `git diff
--check` passed, and the full deterministic suite passed (`3840/3840`; L1
`986/986`, Codex L1 `445/445`, L4 `2209/2209`, L5 `200/200`; toolchain
preflight ok).

## Feature Status
`Completed / Archived`. The active spec folder is removed from `specs/**`; the
completed implementation status lives in project memory and this archive
report. Public native-platform release claims remain blocked by the preserved
UAT matrix.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, generated payload metadata/path references, active spec
inventory, and test fixture locations. It does not relax the Python runner
runtime contract, public claim limits, safe repair boundary, or UAT gate.

## Conflicts Resolved
- Layer 4 gate tests referenced XPLAT-008 schemas under the active spec
  directory. The schemas were copied to
  `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/` and
  tests were repointed before removing the active spec folder.
- XPLAT-008 release-readiness defaults and fixtures referenced UAT evidence
  under the active spec folder. The release packet, UAT matrix, and partial
  Codex/macOS UAT detail were copied to `docs/ai/specs/.process/`, and default
  evidence paths were repointed there.
- The roadmap and MOC still described XPLAT-008 as in progress after PR #292
  merged. This cleanup marks XPLAT-008 archived while keeping public native
  platform release claims blocked by operator UAT.
- Full-suite verification exposed a worktree-only parity gap where the Python
  read-only helper rejected same-repo `.git/worktrees/<id>` metadata names while
  the Bash reference reported the active branch. The helper now accepts that
  bounded Git worktree shape and has regression coverage.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-008-claude-codex-cutover-universal-install-release-gate`
- **cleanupBranch**: `codex/xplat-008-archive-cleanup`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for the XPLAT lane.
- Only one active merged spec folder was present: XPLAT-008.
- Historical workflow/design process files under `docs/ai/specs/.process/`
  were preserved.
- Release-readiness/UAT evidence was preserved outside active `specs/**`
  because it remains the durable public-release blocker.

## Scoping
Full archive + cleanup for XPLAT-008. The active
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/` folder
is removed and recoverable via the commands above. XPLAT-001 through XPLAT-008
are archived; public native Windows/macOS/Linux release claims remain blocked
until real operator UAT evidence passes.
