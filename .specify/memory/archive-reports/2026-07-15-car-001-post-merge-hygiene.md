# Archival Report - CAR-001 Candidate Route Baseline and Role Contracts

## Mode
- **archiveMode**: single-feature post-merge cleanup
- **dryRun**: false (`$speckit-pro:speckit-archive-cleanup all merged and completed specs`)
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true

## Sweep Summary
| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/car-001-candidate-route-baseline` | eligibleForArchive -> archived | removed (cleanup applied) | PR #350 merged into `main` with CAR-001's two research deliverables and roadmap handoff; CAR-002 is now unblocked |
| `specs/xplat-003-supply-chain-security-and-consumer-trust-model` | already archived | local empty directory residue removed | XPLAT-003 was already archived in `.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`; no tracked files remained |

## Excluded Current Spec
`None` (CAR-001 is merged; cleanup runs from current `main` on
`codex/archive-completed-specs-20260715`)

## Provenance
- **Source spec path**: `specs/car-001-candidate-route-baseline/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/350
- **PR title**: `docs(speckit-pro): add the Claude agent route-candidate research baseline`
- **Merged at**: `2026-07-15T13:42:16Z`
- **Merge commit**: `725be949b856724a073622900bd168d29b2f4603`
- **Head branch**: `car-001-candidate-route-baseline`
- **Base branch**: `main`
- **Workflow file**: `docs/ai/specs/.process/CAR-001-workflow.md`
- **Design concept**: `docs/ai/specs/.process/CAR-001-design-concept.md`
- **CI / metadata gates**: PR #350 checks passed, including `test (speckit-pro)`, `validate-plugins`, `validate-pr-title`, `validate-release-note`, `validate-docs`, `validate-workflows`, CodeQL, and Linux container preflight checks.
- **Artifact manifest**: `docs/ai/research/claude-agent-route-candidate-manifest.json`
- **Screenshot retention**: N/A - CAR-001 is a documentation research spike.
- **Expiration risk**: committed source/process evidence and GitHub check URLs have no repository-retention dependency.

## Feature Summary
CAR-001 shipped the dated Claude agent route-candidate baseline for the
CAR-001..CAR-011 routing sequence. It added a human-readable research record
and a provisional machine-readable manifest covering all twelve named agents:
the eleven current Claude agents plus the `autopilot-fast-helper` contract
translated from the Codex helper source.

The merged work inventories route-policy-bearing source, skill, validation,
generated-payload, and installed-cache surfaces; pins the immutable production
comparator to `speckit-pro-v2.19.1` at
`e343aa2e4ebcb2d48c501f285d7072cfd55722da`; records candidate model/effort
tuples and role contracts; separates project-level eligibility from
environment-time availability; records capability questions for CAR-002; labels
current Layer 6 Claude evaluation as bare prompt emulation/non-release
evidence; and keeps all executable-route claims deferred until probing and
qualification.

## Canonical Artifacts
- `docs/ai/research/claude-agent-route-candidates.md`
- `docs/ai/research/claude-agent-route-candidate-manifest.json`
- `docs/ai/specs/.process/CAR-001-workflow.md`
- `docs/ai/specs/.process/CAR-001-design-concept.md`
- `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
- `docs/ai/specs/claude-agent-routing-roadmap-MOC.md`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`

## Recovery Commands
```text
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/spec.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/plan.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/tasks.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/research.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/data-model.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/quickstart.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/contracts/agent-route-candidate-manifest.schema.json
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/requirements.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/traceability.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/research-rigor.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/data-integrity.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/SPEC-MOC.md
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/specs/.process/CAR-001-workflow.md
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/specs/.process/CAR-001-design-concept.md
git checkout 725be949b856724a073622900bd168d29b2f4603 -- specs/car-001-candidate-route-baseline
```

## Changed Files
| File | Change Summary |
|------|----------------|
| `.specify/memory/changelog.md` | Appended CAR-001 provenance, shipped-artifact summary, and recovery commands |
| `.specify/memory/spec.md` | Appended CAR-001 product summary, requirements preserved, success criteria, and cleanup note |
| `.specify/memory/plan.md` | Appended CAR-001 technical approach, verification strategy, and cleanup note |
| `.specify/memory/archive-reports/2026-07-15-car-001-post-merge-hygiene.md` | This report |
| `GEMINI.md` | Added CAR-001 archive note and updated last-updated date |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` | Marked CAR-001 archived and moved CAR-002 to ready |
| `docs/ai/specs/claude-agent-routing-roadmap-MOC.md` | Updated roadmap status and regenerated active-spec index |
| `docs/ai/specs/.process/autopilot-state.json` | Marked CAR-001 as latest post-merge archived state |
| `specs/car-001-candidate-route-baseline/` | Removed from active `specs/**` after archive |

## Post-Cleanup Verification
- PASS: `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json /tmp/car-001-autopilot-state-json-tool.json`
- PASS: `generate-spec-index-write` runner request in apply mode; touched `docs/ai/specs/claude-agent-routing-roadmap-MOC.md`
- PASS: `generate-spec-index-check` runner request; all in-scope maps up to date
- PASS: `find specs -mindepth 1 -maxdepth 4 -print` -> `specs/.gitkeep`
- PASS: `git diff --check`
- PASS: `python3 tests/speckit-pro/run-all.py --layer 1` -> `1427/1427`

## Feature Status
`Completed / Archived`. The active `specs/car-001-candidate-route-baseline/`
folder was removed from `specs/**`; completed status now lives in project
memory, the CAR roadmap, and this archive report.

## Constitution Compliance
PASS. This cleanup changes archive memory, roadmap/MOC status, generated
SpecKit index state, process state, and active spec inventory only. It does not
change plugin runtime behavior, generated payload behavior, release automation,
or installed-user behavior.

## Conflicts Resolved
- The active CAR-001 `spec.md` still said `Draft`, and `tasks.md` checkboxes
  remained unchecked, but PR #350 merged the deliverables and all PR checks
  passed. The merge record controls archive eligibility.
- The roadmap still showed CAR-001 in review and CAR-002 blocked; this cleanup
  marks CAR-001 complete/archived and CAR-002 ready.

## Cleanup Decision
- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/car-001-candidate-route-baseline`
- **cleanupBranch**: `codex/archive-completed-specs-20260715`
- **blockedBy**: none
- **Recovery**: see the Recovery Commands above

## Defaults Applied
- Mode defaulted to post-merge archive cleanup for all merged/completed active specs.
- Scope defaulted to archival artifacts, roadmap/MOC status, autopilot state,
  generated index refresh, and completed active-spec folder removal.

## Scoping
Full archive + cleanup for CAR-001. Historical
`docs/ai/specs/.process/CAR-001-*` files are preserved. The already archived
XPLAT-003 active directory had no tracked files and was removed only as local
empty-directory residue.
