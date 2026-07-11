# Archival Report - XPLAT-009 Plugin Source and Payload Bash Eradication

## Mode
- **archiveMode**: sweep (`--sweep --current-target specs/xplat-010-repository-bash-confinement`)
- **dryRun**: false
- **applyCleanupRequested**: true (operator-directed pre-flight cleanup for the XPLAT-010 run)
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-009-plugin-source-and-payload-bash-eradication` | eligibleForArchive -> archived | removed (cleanup applied) | XPLAT-009 merged via PR #297 (merge commit `7bc6be1a9faaa3113f8db903188ddb49a445e7ce`, an ancestor of this branch; local spec dir byte-identical to the merged content) and shipped in speckit-pro 2.18.0; roadmap plan PR #295 and Windows interpreter follow-up PR #299 are also merged |
| `specs/xplat-010-repository-bash-confinement` | excludedCurrentSpec | none | Current target of this run; excluded from archival and cleanup |

## Excluded Current Spec
`specs/xplat-010-repository-bash-confinement`

## Provenance
| PR | Title | Merged at | Merge commit | Head branch |
|----|-------|-----------|--------------|-------------|
| [#295](https://github.com/racecraft-lab/racecraft-plugins-public/pull/295) | `docs(xplat): plan Bash eradication backstop` | `2026-07-07T14:40:51Z` | `bb744db61fe569514c5b856bc4b20cbf478fd8d0` | roadmap planning PR that added XPLAT-009/XPLAT-010 |
| [#297](https://github.com/racecraft-lab/racecraft-plugins-public/pull/297) | `feat(xplat): eradicate plugin Bash runtime surface` | `2026-07-08T20:05:01Z` | `7bc6be1a9faaa3113f8db903188ddb49a445e7ce` | `codex/xplat-009-plugin-source-and-payload-bash-eradication` |
| [#299](https://github.com/racecraft-lab/racecraft-plugins-public/pull/299) | `fix(runner): resolve python interpreter and home directory on windows` | `2026-07-08T22:44:29Z` | `fa7cd5671a40350e8a3feb9a13ebc3900591eef1` | post-merge follow-up fix |

- **Source spec path**: `specs/xplat-009-plugin-source-and-payload-bash-eradication/` (repo-relative)
- **Workflow file**: `docs/ai/specs/.process/XPLAT-009-workflow.md`
- **Design concept**: `docs/ai/specs/.process/XPLAT-009-design-concept.md`
- **Preserved guard/proof evidence**: `docs/ai/specs/.process/XPLAT-009-source-inventory.md`, `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`, `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`, `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`, `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`, `docs/ai/specs/.process/XPLAT-009-retrospective.md`
- **Release**: speckit-pro 2.18.0 (`speckit-pro/CHANGELOG.md` 2026-07-08)
- **Base branch**: `main`
- **CI run URL**: N/A - merge commits are durable source references
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Metadata gates**: PR #297 checks reported green before merge (CodeQL, `test (speckit-pro)`, merge state CLEAN per the XPLAT-009 run record)
- **Screenshot retention**: N/A (no visual artifacts)
- **Expiration risk**: None for committed repository state; guard and release evidence is preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-009 removed the remaining plugin-source Bash substrate while preserving
the XPLAT-008 installed-runtime contract of direct Python 3.11+
`speckit_pro_runner` invocation. The merged implementation ported active
plugin-source script behavior to Python runner/helper/gate operations, deleted
the remaining live `.sh` files under `speckit-pro/`, replaced active Bash
instructions in skill and agent guidance, rebuilt generated Claude and Codex
payloads from source, and proved source, generated payloads, and a bounded
installed-cache artifact pass one Python-backed zero-Bash guard with a
reviewable historical allowlist and seeded regression coverage.

Repository-wide Bash confinement outside the plugin package (top-level
`tests/**`, top-level `scripts/**`, hooks outside the plugin, `.specify/**`,
and the CI dispatch guard) is XPLAT-010, the current in-progress target of this
run. Public native Windows/macOS/Linux support claims remain blocked by the
preserved XPLAT-008 UAT matrix.

## Canonical Artifacts
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `scripts/refresh-release-artifacts.py`
- `docs/ai/specs/.process/XPLAT-009-workflow.md`
- `docs/ai/specs/.process/XPLAT-009-design-concept.md`
- `docs/ai/specs/.process/XPLAT-009-source-inventory.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-009-retrospective.md`
- `docs/ai/specs/.process/XPLAT-009-pr-packet.json`
- `docs/ai/specs/.process/XPLAT-009-pr-body.md`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/`
- `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/contracts/`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py`

## Recovery Commands
```text
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/plan.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/tasks.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/research.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/data-model.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/quickstart.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/SPEC-MOC.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/checklists/integration.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/checklists/reliability.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/checklists/requirements.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/checklists/security.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/historical-allowlist-entry.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/installed-cache-proof.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-request.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-result.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/uat-runbook.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/final-reviewability/gate-state.json
git checkout 7bc6be1a9faaa3113f8db903188ddb49a445e7ce -- specs/xplat-009-plugin-source-and-payload-bash-eradication
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-009 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-009 product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-009 technical approach, verification strategy, and cleanup note |
| `.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-009 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-009 complete/archived and XPLAT-010 in progress |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-009 link with archive and preserved-evidence pointers; removed the archived entry from the generated index |
| `docs/ai/specs/.process/autopilot-state.json` | Marked the XPLAT-009 run as post-merge archived state |
| `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/contracts/` | Preserved XPLAT-009 contract schemas needed by Layer 4 gate coverage after cleanup (git mv from the active spec dir) |
| `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` | Repointed XPLAT-009 contract reads away from active `specs/**` |
| `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` | Removed the archived XPLAT-009 spec path from active-path allow-list coverage |
| `specs/xplat-009-plugin-source-and-payload-bash-eradication/` | Removed from active `specs/**` after archive |

## Feature Status
`Completed / Archived`. The active spec folder is removed from `specs/**`; the
completed implementation status lives in project memory and this archive
report. Repository-wide Bash confinement continues as XPLAT-010 on
`xplat-010-repository-bash-confinement`, and public native-platform release
claims remain blocked by the preserved XPLAT-008 UAT matrix.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, active spec inventory, and test fixture locations. It does not
change runner source, generated payloads, the zero-Bash guard, public claim
limits, or any release gate behavior.

## Conflicts Resolved
- Layer 4 gate tests read the XPLAT-009 contract schemas from the active spec
  directory (`XPLAT_009_CONTRACT_DIR` in
  `tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py`). The four
  schemas were moved to
  `tests/speckit-pro/layer4-scripts/fixtures/xplat-009-zero-bash/contracts/`
  and the test was repointed before removing the active spec folder.
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` allow-listed
  the active XPLAT-009 spec path in `allowed_xplat009_prefixes`; the archived
  path was removed from coverage, matching the XPLAT-008 archive precedent.
- The roadmap and MOC still described XPLAT-009 as in progress and XPLAT-010 as
  blocked after PR #297 merged. Both now record XPLAT-009 as complete/archived
  and XPLAT-010 as the in-progress current target.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-009-plugin-source-and-payload-bash-eradication` (after `git mv` of the four contract schemas into the fixture tree)
- **cleanupBranch**: `xplat-010-repository-bash-confinement` (feature worktree; the repository's protected `main` is never cleaned directly — archive commits land through squash-merged PRs, matching every prior archive report)
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Sweep mode ran as the operator-directed XPLAT-010 pre-flight with apply
  cleanup enabled; the current target `specs/xplat-010-repository-bash-confinement`
  was excluded from all actions.
- Only one previously merged spec folder was present: XPLAT-009.
- Historical workflow/design/guard evidence under `docs/ai/specs/.process/`
  was preserved unchanged.
- The spec-level `.process/` residue (UAT runbook, final-reviewability state)
  was removed with the spec folder and remains recoverable via the merge
  commit, matching the XPLAT-008 precedent.

## Scoping
Full archive + cleanup for XPLAT-009 only. The active
`specs/xplat-009-plugin-source-and-payload-bash-eradication/` folder is removed
and recoverable via the commands above. XPLAT-001 through XPLAT-009 are
archived; XPLAT-010 is in progress; public native Windows/macOS/Linux release
claims remain blocked until real operator UAT evidence passes the preserved
XPLAT-008 matrix.
