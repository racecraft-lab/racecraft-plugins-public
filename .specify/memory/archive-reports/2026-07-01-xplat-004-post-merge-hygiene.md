# Archival Report - XPLAT-004 Cross-Platform Runner Foundation

## Mode
- **archiveMode**: single-feature cleanup from `all merged specs`
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup all merged specs`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-004-cross-platform-runner-foundation` | eligibleForArchive -> archived | removed (cleanup applied) | Merged via PR #274 (`cef3ed26`); durable runner source, metadata, tests, and fixtures now live outside active `specs/**` |

## Excluded Current Spec
`None` (`all merged specs` cleanup runs from current `origin/main` after PR #274 merged)

## Provenance
- **Source spec path**: `specs/xplat-004-cross-platform-runner-foundation/` (repo-relative)
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/274
- **PR title**: `feat(XPLAT-004): Add cross-platform runner foundation`
- **Merged at**: `2026-07-01T22:13:40Z`
- **Merge commit**: `cef3ed260dabf73833d3de82f82cacdb2c7758fa`
- **Head branch**: `codex/xplat-004-cross-platform-runner-foundation`
- **Base branch**: `main`
- **CI run URL**: N/A - PR merge commit is the durable source reference
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Expiration risk**: None for committed repository state; process files are preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-004 shipped the source-checkout Python 3.11+ standard-library runner
foundation selected by XPLAT-002 and bounded by XPLAT-003. The merged work added
the `speckit_pro_runner` package, module-style invocation through
`python -m speckit_pro_runner`, JSON envelope validation, runtime-info and
preflight operations, typed path and subprocess fixture primitives, source
checksum/manifest metadata, and focused Layer 4 runner tests.

The spec intentionally did not port real helper behavior, update active Claude
Code or Codex skills/hooks/generated payloads, prove installed-cache launch, run
native matrix UAT, or make public platform support claims. XPLAT-005 now owns
read-only helper parity on the runner. XPLAT-006 owns mutation/install/PR
emission helper ports. XPLAT-007 owns active cutover, generated payload proof,
installed-cache proof, native Windows/macOS/Linux UAT, update/autoheal proof,
and public release claims.

## Canonical Artifacts
- `speckit-pro/speckit_pro_runner/__init__.py`
- `speckit-pro/speckit_pro_runner/__main__.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- `tests/speckit-pro/unit/test-speckit-pro-runner.sh`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/contract-fixtures.json`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/runner-foundation-changed-files.txt`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/platform-runbook-fixtures.md`
- `docs/ai/specs/.process/XPLAT-004-workflow.md`
- `docs/ai/specs/.process/XPLAT-004-design-concept.md`

## Recovery Commands
```text
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/spec.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/plan.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/tasks.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/research.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/data-model.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/quickstart.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/contracts/runner-envelope.schema.json
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/contracts/runner-manifest.schema.json
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/.process/full-verification-evidence.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/.process/uat-runbook.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/SPEC-MOC.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-workflow.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-design-concept.md
git checkout cef3ed260dabf73833d3de82f82cacdb2c7758fa -- specs/xplat-004-cross-platform-runner-foundation
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-004 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-004 product summary, requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-004 technical approach, verification strategy, boundaries, and cleanup note |
| `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-004 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-004 archived and XPLAT-005 ready |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-004 link with an archive pointer |
| `docs/ai/specs/.process/autopilot-state.json` | Marked XPLAT-004 as post-merge archived state |
| `tests/speckit-pro/unit/test-speckit-pro-runner.py` | Repointed runbook fixture lookup away from active `specs/**` |
| `tests/speckit-pro/unit/fixtures/speckit-pro-runner/runner-foundation-changed-files.txt` | Preserved the XPLAT-004 changed-file fallback fixture for Layer 4 after spec cleanup |
| `tests/speckit-pro/unit/fixtures/speckit-pro-runner/platform-runbook-fixtures.md` | Preserved the XPLAT-004 runbook fixture contract for Layer 4 after spec cleanup |
| `specs/xplat-004-cross-platform-runner-foundation/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `node docs-site/scripts/generate-reference-pages.mjs`
- `node docs-site/scripts/generate-reference-pages.mjs --check`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `tests/speckit-pro/unit/test-speckit-pro-runner.sh`
- `git diff --check`
- `bash tests/speckit-pro/run-all.sh --layer 1`
- `bash tests/speckit-pro/run-all.sh --layer 4`

Result: pass. `find specs` reported only `specs/.gitkeep`; runner test reported
`9/9 passed`; Layer 1 structural validation reported `1443/1443 passed`; Layer
4 script validation reported `2101/2101 passed`.

## Feature Status
`Completed / Archived`. The active spec folder was removed from `specs/**`; the
completed status now lives in project memory and this archive report.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, active spec inventory, and a test fixture location only. It does
not change installed plugin runtime behavior, generated payload behavior,
release automation, or public platform claims.

## Conflicts Resolved
- The merged XPLAT-004 runner test referenced
  `specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md`.
  It also used `specs/xplat-004-cross-platform-runner-foundation/.process/changed-files.txt`
  as a fallback when Git diff context is unavailable. Both fixtures were copied
  to the Layer 4 fixture tree before active spec cleanup so tests remain
  independent of archived `specs/**` content.
- The roadmap and MOC still described XPLAT-004 as scaffolded/in progress after
  PR #274 merged. This cleanup marks XPLAT-004 archived and XPLAT-005 ready.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-004-cross-platform-runner-foundation`
- **cleanupBranch**: `codex/archive-xplat-004-post-merge-hygiene`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for all merged active specs.
- Only one active merged spec folder was present: XPLAT-004.
- Historical process files under `docs/ai/specs/.process/` were preserved.

## Scoping
Full archive + cleanup for XPLAT-004. The active
`specs/xplat-004-cross-platform-runner-foundation/` folder is removed and
recoverable via the commands above. Other XPLAT specifications are already
archived or still pending and were not removed.
