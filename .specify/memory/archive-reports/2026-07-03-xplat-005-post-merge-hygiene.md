# Archival Report - XPLAT-005 Read-Only Helper Port

## Mode
- **archiveMode**: single-feature cleanup from `XPLAT`
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup XPLAT`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-005-read-only-helper-port` | eligibleForArchive -> archived | removed (cleanup applied) | Merged via PR #276 (`c4642f50`); durable helper source, metadata, tests, and fixtures now live outside active `specs/**` |

## Excluded Current Spec
`None` (PR #276 is merged; cleanup runs from `origin/main` in a dedicated branch)

## Provenance
- **Source spec path**: `specs/xplat-005-read-only-helper-port/` (repo-relative)
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/276
- **PR title**: `feat(XPLAT-005): Add read-only helper port`
- **Merged at**: `2026-07-03T03:16:56Z`
- **Merge commit**: `c4642f50ae99172170798a49f0c8fd990891c0f9`
- **Head branch**: `codex/xplat-005-read-only-helper-port`
- **Base branch**: `main`
- **CI run URL**: N/A - PR merge commit is the durable source reference
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Expiration risk**: None for committed repository state; process files are preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-005 shipped the first real read-only/advisory helper behavior ports on
the Python 3.11+ standard-library runner foundation. The merged work added the
helper registry, read-only helper module, envelope/runtime integration,
Python-authoritative helper records, deterministic runner request fixtures,
source-checkout Bash-reference parity comparisons, synthetic path coverage,
malformed-input coverage, runner metadata refresh, and Layer 4 helper gates.

The feature intentionally did not switch active Claude Code or Codex skills,
hooks, generated payloads, install behavior, public documentation claims,
write/regenerate modes, PR body generation, PR emission, split state, restack,
artifact relocation, install repair, autoheal, or user-local mutation behavior.
XPLAT-006 owns mutation, install, restack, state-writing, and PR-emission helper
ports. XPLAT-007 owns active cutover, generated payload proof, installed-cache
proof, native Windows/macOS/Linux UAT, update/autoheal proof, and public release
claims.

## Canonical Artifacts
- `speckit-pro/speckit_pro_runner/helpers/__init__.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/fixture-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/`
- `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/`
- `docs/ai/specs/.process/XPLAT-005-workflow.md`
- `docs/ai/specs/.process/XPLAT-005-design-concept.md`

## Recovery Commands
```text
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/spec.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/plan.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/tasks.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/research.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/data-model.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/quickstart.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/read-only-helper-request.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/helper-promotion-record.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/checklists/requirements.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/checklists/integration.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/checklists/error-handling.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/checklists/reliability.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/checklists/security.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/uat-runbook.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/pr-packets/xplat-005-read-only-helper-port.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/pr-packets/xplat-005-read-only-helper-port.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/final-reviewability/gate-state.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/SPEC-MOC.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-workflow.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-design-concept.md
git checkout c4642f50ae99172170798a49f0c8fd990891c0f9 -- specs/xplat-005-read-only-helper-port
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-005 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-005 product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-005 technical approach, verification strategy, boundaries, and cleanup note |
| `.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-005 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-005 archived and XPLAT-006 ready |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-005 link with an archive pointer and marked XPLAT-006 ready |
| `docs/ai/specs/.process/autopilot-state.json` | Marked XPLAT-005 as post-merge archived state |
| `docs-site/src/content/docs/reference/tests.md` | Refreshed generated test reference content after preserving XPLAT-005 fixture inputs |
| `speckit-pro/speckit_pro_runner/helpers/read_only.py` | Aligned the no-active-map `generate-spec-index --check` helper response with the Bash `--check` output |
| `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | Refreshed runner source metadata after the read-only helper edge-case fix |
| `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256` | Refreshed runner source checksum after the read-only helper edge-case fix |
| `tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` | Repointed read-only helper parity tests away from active `specs/**` |
| `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/requests/` | Repointed feature-dir request fixtures to the preserved XPLAT-005 fixture inputs |
| `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/bash-reference-manifest.json` | Repointed Bash-reference comparisons to the preserved XPLAT-005 fixture inputs |
| `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/xplat-005-feature/` | Preserved minimal XPLAT-005 spec inputs needed by Layer 4 helper parity coverage after cleanup |
| `specs/xplat-005-read-only-helper-port/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `bash tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.sh`
- `git diff --check`
- `bash tests/speckit-pro/run-all.sh --layer 1`
- `bash tests/speckit-pro/run-all.sh --layer 4`
- `corepack pnpm reference:generate` from `docs-site/`
- `corepack pnpm reference:check` from `docs-site/`
- `corepack pnpm validate:quality` from `docs-site/`

Result: pass. `find specs` reported only `specs/.gitkeep`; focused read-only
helper tests reported `32/32 passed`; Layer 1 structural validation reported
`1443/1443 passed`; Layer 4 script validation reported `2135/2135 passed`;
docs reference and quality checks passed after regenerating the tests reference
page.

## Feature Status
`Completed / Archived`. The active spec folder was removed from `specs/**`; the
completed status now lives in project memory and this archive report.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, active spec inventory, and test fixture locations only. It does
not change installed plugin runtime behavior, generated payload behavior,
release automation, active Claude/Codex invocation paths, mutation helpers, or
public platform claims.

## Conflicts Resolved
- The merged XPLAT-005 read-only helper tests and request fixtures referenced
  `specs/xplat-005-read-only-helper-port`. The minimal fixture inputs needed by
  `count-markers`, `validate-gate`, `estimate-reviewable-loc`, `o5-topology`,
  `atomicity-route`, and `plan-layers` were copied to the Layer 4 fixture tree
  before active spec cleanup so tests remain independent of archived
  `specs/**` content.
- Removing the last active XPLAT spec exposed a no-active-map parity edge case:
  the Python read-only helper for `generate-spec-index --check` returned the
  write-mode "no maps needed regenerating" wording while its declared argv and
  Bash reference used `--check`. The helper now returns the Bash `--check`
  wording, and runner metadata was refreshed.
- The roadmap and MOC still described XPLAT-005 as in progress after PR #276
  merged. This cleanup marks XPLAT-005 archived and XPLAT-006 ready.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-005-read-only-helper-port`
- **cleanupBranch**: `codex/xplat-005-archive-cleanup`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for the XPLAT lane.
- Only one active merged spec folder was present: XPLAT-005.
- Historical process files under `docs/ai/specs/.process/` were preserved.

## Scoping
Full archive + cleanup for XPLAT-005. The active
`specs/xplat-005-read-only-helper-port/` folder is removed and recoverable via
the commands above. XPLAT-001 through XPLAT-004 are already archived; XPLAT-006
is now ready and XPLAT-007 remains pending.
