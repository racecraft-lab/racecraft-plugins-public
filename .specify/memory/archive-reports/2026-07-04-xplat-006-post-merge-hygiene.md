# Archival Report - XPLAT-006 Mutation, Install, and PR-Emission Helper Port

## Mode
- **archiveMode**: single-feature cleanup from `all merged specs`
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup all merged specs`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-006-mutation-install-pr-emission-helper-port` | eligibleForArchive -> archived | removed (cleanup applied) | Merged via PR #281 (`85e79cd4`); durable runner helper source, install inventory, fixtures, schemas, and process evidence now live outside active `specs/**` |

## Excluded Current Spec
`None` (PR #281 is merged; cleanup runs from `origin/main` in a dedicated branch)

## Provenance
- **Source spec path**: `specs/xplat-006-mutation-install-pr-emission-helper-port/` (repo-relative)
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/281
- **PR title**: `feat(XPLAT-006): Add mutation, install, and PR-emission helper port`
- **Merged at**: `2026-07-04T03:59:03Z`
- **Merge commit**: `85e79cd4b5ccc0116a2c5cdd0f04ce274294075f`
- **Head branch**: `codex/xplat-006-mutation-install-pr-emission-helper-port`
- **Base branch**: `main`
- **CI run URL**: N/A - PR merge commit is the durable source reference
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Expiration risk**: None for committed repository state; process files are preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-006 shipped the mutation-capable Python runner helper substrate after the
XPLAT-004 runner foundation and XPLAT-005 read-only registry. The merged work
added mutation request/result handling, atomic write primitives, dirty-worktree
guards, path-boundary and fake-home repair checks, install inventory and
doctor/preflight classifications, generated PR-body output, fake command-plan
proof for PR emission, promotion records, deferred live-mutation diagnostics,
and focused Layer 4 mutation-helper tests.

The feature also shipped the Codex autopilot phase-coverage hardening requested
after the XPLAT-006 autopilot run: a Python validator, generated payload
mirrors, and deterministic tests that reject missing Phase 6.5, missing Post
items, duplicate/in-progress state errors, collapsed later phase labels, and
malformed `autopilot-state.json`.

XPLAT-006 intentionally did not switch active Claude Code or Codex invocation
paths, generated-payload selection/cutover behavior, repo-local release gates,
native installed-cache UAT, update/autoheal proof, or public platform support
claims. XPLAT-007 now owns active repo-local Bash helper/test/eval/build/release
gate migration to Python. XPLAT-008 owns Claude/Codex cutover and universal
install/full-use/update/autoheal release readiness.

## Canonical Artifacts
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- `speckit-pro/speckit_pro_runner/helpers/promotion.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/install_inventory.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md`
- `dist/codex/speckit-pro/skills/speckit-autopilot/`
- `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py`
- `tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/`
- `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/`
- `docs/ai/specs/.process/XPLAT-006-workflow.md`
- `docs/ai/specs/.process/XPLAT-006-design-concept.md`

## Recovery Commands
```text
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/plan.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/tasks.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/research.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/data-model.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/quickstart.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-request.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-result.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/doctor-preflight-result.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/helper-promotion-record.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/autopilot-phase-coverage-report.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/requirements.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/integration.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/reliability.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/error-handling.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/checklists/security.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/uat-runbook.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/xplat-006-pr-packet/packet.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/xplat-006-pr-packet/body.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/pr-packets/packet/validation.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/marker-plan/final-marker-split-result.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/SPEC-MOC.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:docs/ai/specs/.process/XPLAT-006-workflow.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:docs/ai/specs/.process/XPLAT-006-design-concept.md
git checkout 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f -- specs/xplat-006-mutation-install-pr-emission-helper-port
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-006 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-006 product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-006 technical approach, verification strategy, boundaries, and cleanup note |
| `.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-006 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-006 archived and XPLAT-007 ready |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-006 link with an archive pointer and marked XPLAT-007 ready |
| `docs/ai/specs/.process/autopilot-state.json` | Marked XPLAT-006 as post-merge archived state |
| `tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py` | Repointed phase-coverage schema lookup away from active `specs/**` |
| `tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` | Repointed mutation-helper schema lookup away from active `specs/**` |
| `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/` | Preserved XPLAT-006 contract schemas needed by Layer 4 helper coverage after cleanup |
| `specs/xplat-006-mutation-install-pr-emission-helper-port/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py`
- `python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py`
- `git diff --check`
- `bash tests/speckit-pro/run-all.sh`

Result: pass. `find specs` reported only `specs/.gitkeep`; phase-coverage tests
reported `8/8 passed`; mutation-helper tests reported `17/17 passed`; the
active workflow/state pair returned `status=pass`; docs reference pages were
current; and the default deterministic suite reported `3803/3803 passed`.

## Feature Status
`Completed / Archived`. The active spec folder is removed from `specs/**`; the
completed status lives in project memory and this archive report.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, active spec inventory, and test fixture locations only. It does
not change installed plugin runtime behavior, generated payload behavior,
release automation, active Claude/Codex invocation paths, mutation helper
behavior, or public platform claims.

## Conflicts Resolved
- The merged XPLAT-006 Layer 4 mutation and phase-coverage tests referenced
  contract schemas under the active spec directory. The schemas were copied to
  `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/contracts/` and
  the tests were repointed before removing the active spec folder.
- The roadmap and MOC still described XPLAT-006 as in progress after PR #281
  merged. This cleanup marks XPLAT-006 archived and XPLAT-007 ready.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-006-mutation-install-pr-emission-helper-port`
- **cleanupBranch**: `codex/archive-merged-specs-20260704`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for all merged active specs.
- Only one active merged spec folder was present on current `origin/main`: XPLAT-006.
- Historical process files under `docs/ai/specs/.process/` were preserved.

## Scoping
Full archive + cleanup for XPLAT-006. The active
`specs/xplat-006-mutation-install-pr-emission-helper-port/` folder is removed
and recoverable via the commands above. XPLAT-001 through XPLAT-005 are already
archived; XPLAT-007 is ready; XPLAT-008 remains pending.
