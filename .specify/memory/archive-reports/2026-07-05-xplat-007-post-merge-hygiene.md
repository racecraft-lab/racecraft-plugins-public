# Archival Report - XPLAT-007 Python Tooling and Release-Gate Migration

## Mode
- **archiveMode**: single-feature cleanup from `XPLAT`
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup XPLAT`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/xplat-007-python-tooling-and-release-gate-migration` | eligibleForArchive -> archived | removed (cleanup applied) | XPLAT-007 merged across PRs #284, #285, #286, and #287; durable Python gate source, workflows, fixtures, promotion records, and process evidence now live outside active `specs/**` |

## Excluded Current Spec
`None` (XPLAT-007 implementation PRs are merged; cleanup runs from `origin/main` on `codex/xplat-007-archive-cleanup`)

## Provenance
| PR | Title | Merged at | Merge commit | Head branch |
|----|-------|-----------|--------------|-------------|
| [#284](https://github.com/racecraft-lab/racecraft-plugins-public/pull/284) | `feat(XPLAT-007): Add gate dispatch foundation` | `2026-07-05T17:16:16Z` | `6c0af6cf6cd53e1569bcb03c9a56d939360a4b24` | `XPLAT-007-python-tooling-and-release-gate-migration/01-foundation` |
| [#285](https://github.com/racecraft-lab/racecraft-plugins-public/pull/285) | `feat(XPLAT-007): Update Python repo-local gate runner` | `2026-07-05T18:08:14Z` | `cb1697290b8f7cb289d0740e59c899285dc95c33` | `XPLAT-007-python-tooling-and-release-gate-migration/02-us1` |
| [#286](https://github.com/racecraft-lab/racecraft-plugins-public/pull/286) | `feat(XPLAT-007): Update payload install release gates` | `2026-07-05T18:34:53Z` | `a0d2dd015f0a33e85634256061926e5274fdb69a` | `XPLAT-007-python-tooling-and-release-gate-migration/03-us2` |
| [#287](https://github.com/racecraft-lab/racecraft-plugins-public/pull/287) | `feat(speckit-pro): Update Review Active No-Shell Guardrails` | `2026-07-05T18:57:01Z` | `0ff2d8d731698cde02b334cdc3b2a377216b5d45` | `XPLAT-007-python-tooling-and-release-gate-migration/04-us3` |

- **Source spec path**: `specs/xplat-007-python-tooling-and-release-gate-migration/` (repo-relative)
- **Workflow file**: `docs/ai/specs/.process/XPLAT-007-workflow.md`
- **Design concept**: `docs/ai/specs/.process/XPLAT-007-design-concept.md`
- **Base branch**: `main`
- **CI run URL**: N/A - merge commits are durable source references
- **Artifact manifest**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- **Checksum file**: `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- **Expiration risk**: None for committed repository state; process files are preserved in `docs/ai/specs/.process/`

## Feature Summary
XPLAT-007 shipped the active repo-local Python gate migration needed before the
Claude/Codex installed-plugin cutover. The merged work added the
`speckit_pro_runner.gates` package, Python-authoritative suite, payload,
install-verification, release-readiness, and active-path guard operations,
runner dispatch wiring, promotion records, request fixtures, payload and install
case fixtures, release-readiness evidence, no-shell guard cases, CI dispatch
updates, maintainer-facing command updates, runner metadata refreshes, and
Layer 4 gate tests.

The feature deliberately did not switch active Claude Code or Codex installed
runtime invocation paths, rebuild generated release payloads for publication,
publish public platform support claims, run native installed-plugin UAT, or
claim update/autoheal readiness. XPLAT-008 owns those final public-release
gates.

## Canonical Artifacts
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `CLAUDE.md`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs-site/src/content/docs/reference/tests.md`
- `speckit-pro/speckit_pro_runner/gates/__init__.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/suite.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/run-all.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.sh`
- `tests/speckit-pro/unit/test-speckit-pro-gates.py`
- `tests/speckit-pro/unit/fixtures/runner-gates/`
- `tests/speckit-pro/unit/fixtures/runner-gates/contracts/`
- `docs/ai/specs/.process/XPLAT-007-workflow.md`
- `docs/ai/specs/.process/XPLAT-007-design-concept.md`

## Recovery Commands
```text
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/spec.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/plan.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/tasks.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/research.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/data-model.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/SPEC-MOC.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-request.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/promotion-record.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/payload-evidence.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/install-verification-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/release-readiness-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/active-path-guard-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/checklists/requirements.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/checklists/integration.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/checklists/reliability.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/checklists/security.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/checklists/release-readiness.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/.process/marker-plan/pr-marker-plan.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/.process/marker-plan/foundation-checkpoint.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/.process/marker-plan/us1-checkpoint.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/.process/marker-plan/us2-checkpoint.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-workflow.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-design-concept.md
git checkout 0ff2d8d731698cde02b334cdc3b2a377216b5d45 -- specs/xplat-007-python-tooling-and-release-gate-migration
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended XPLAT-007 provenance, summary, canonical artifacts, and recovery commands |
| `.specify/memory/spec.md` | Appended XPLAT-007 product summary, preserved requirements, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended XPLAT-007 technical approach, verification strategy, boundaries, and cleanup note |
| `.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md` | This report |
| `AGENTS.md` | Added XPLAT-007 archive note, active technology entry, and recent-change entry |
| `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` | Marked XPLAT-007 archived and XPLAT-008 ready |
| `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md` | Replaced the active XPLAT-007 link with an archive pointer and marked XPLAT-008 ready |
| `docs/ai/specs/.process/autopilot-state.json` | Marked XPLAT-007 as post-merge archived state |
| `tests/speckit-pro/unit/test-speckit-pro-gates.py` | Repointed XPLAT-007 schema lookup away from active `specs/**` |
| `tests/speckit-pro/unit/fixtures/runner-gates/release-readiness-cases.json` | Repointed a synthetic changed-files fixture away from the removed active spec folder |
| `tests/speckit-pro/unit/fixtures/runner-gates/contracts/` | Preserved XPLAT-007 contract schemas needed by Layer 4 gate coverage after cleanup |
| `specs/xplat-007-python-tooling-and-release-gate-migration/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- `find specs -mindepth 1 -maxdepth 4 -print`
- `python3 tests/speckit-pro/unit/test-speckit-pro-gates.py`
- `git diff --check`
- `node docs-site/scripts/generate-reference-pages.mjs --check`
- `bash tests/speckit-pro/run-all.sh`

Result: pass. `find specs` reported only `specs/.gitkeep`; focused gate tests
reported `31/31 passed`; focused mutation-helper tests reported `17/17 passed`
after disabling local commit signing for temporary test repositories; and the
default deterministic suite reported `3832/3832 passed` with Homebrew Bash
(`PATH=/opt/homebrew/bin:$PATH`) and `GIT_CONFIG_KEY_0=commit.gpgsign` /
`GIT_CONFIG_VALUE_0=false` scoped to the test command. The docs reference
generator reported `Reference pages are current`; the first pnpm wrapper
attempt was blocked by package-manager build-approval policy after dependency
restore, so the underlying Node check was run directly and install side effects
were reverted.

## Feature Status
`Completed / Archived`. The active spec folder is removed from `specs/**`; the
completed status lives in project memory and this archive report.

## Constitution Compliance
PASS. This cleanup changes documentation, process state, archive memory,
roadmap status, active spec inventory, and test fixture locations only. It does
not change installed plugin runtime behavior, generated release payload
selection, public platform claims, native installed-plugin UAT, update, or
autoheal readiness.

## Conflicts Resolved
- The merged XPLAT-007 Layer 4 gate tests referenced contract schemas under the
  active spec directory. The schemas were copied to
  `tests/speckit-pro/unit/fixtures/runner-gates/contracts/` and
  the tests were repointed before removing the active spec folder.
- The roadmap, MOC, and active autopilot state still described XPLAT-007 as in
  progress after PR #287 merged. This cleanup marks XPLAT-007 archived and
  XPLAT-008 ready.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/xplat-007-python-tooling-and-release-gate-migration`
- **cleanupBranch**: `codex/xplat-007-archive-cleanup`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for the XPLAT lane.
- Only one active merged spec folder was present: XPLAT-007.
- Historical process files under `docs/ai/specs/.process/` were preserved.

## Scoping
Full archive + cleanup for XPLAT-007. The active
`specs/xplat-007-python-tooling-and-release-gate-migration/` folder is removed
and recoverable via the commands above. XPLAT-001 through XPLAT-006 are already
archived; XPLAT-008 is now ready and owns Claude/Codex cutover, release payload
publication, native installed-plugin UAT, update/autoheal, and public release
readiness.
